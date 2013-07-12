# Copyright 2009-2013 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from operator import itemgetter
import os.path
from requestbuilder import Arg, MutuallyExclusiveArgList, AUTH, SERVICE
from requestbuilder.auth import QuerySigV2Auth
from requestbuilder.exceptions import AuthError
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.request import AWSQueryRequest
from requestbuilder.service import BaseService
from requestbuilder.util import set_userregion
import shlex
from string import Template
import sys


class EC2CompatibleQuerySigV2Auth(QuerySigV2Auth):
    # -a and -s are deprecated; remove them in 3.2
    ARGS = [Arg('-a', '--access-key', metavar='KEY_ID',
                dest='deprecated_key_id', help=argparse.SUPPRESS),
            Arg('-s', metavar='KEY', dest='deprecated_sec_key',
                help=argparse.SUPPRESS)]

    def preprocess_arg_objs(self, arg_objs):
        # If something else defines '-a' or '-s' args, resolve conflicts with
        # this class's old-style auth args by capitalizing this class's args.
        #
        # This behavior is deprecated and will be removed in version 3.2 along
        # with the -a and -s arguments themselves.
        a_arg_objs = _find_args_by_parg(arg_objs, '-a')
        s_arg_objs = _find_args_by_parg(arg_objs, '-s')
        if len(a_arg_objs) > 1 or len(s_arg_objs) > 1:
            for arg_obj in a_arg_objs:
                if arg_obj.kwargs.get('dest') == 'deprecated_key_id':
                    # Capitalize the "-a"
                    arg_obj.pargs = tuple('-A' if parg == '-a' else parg
                                          for parg in arg_obj.pargs)
            for arg_obj in s_arg_objs:
                if arg_obj.kwargs.get('dest') == 'deprecated_sec_key':
                    # Remove it since regular -S already covers this case
                    arg_objs.remove(arg_obj)

    def configure(self):
        # Old-style CLI args
        # Deprecated; should be removed in 3.2
        if self.args.get('deprecated_key_id'):
            # Use it and complain
            self.args['key_id'] = self.args['deprecated_key_id']
            if _find_args_by_parg(self.ARGS, '-a'):
                msg = ('argument -a/--access-key is deprecated; use '
                       '-I/--access-key-id instead')
            else:
                msg = ('argument -A/--access-key is deprecated; use '
                       '-I/--access-key-id instead')
            self.log.warn(msg)
            print >> sys.stderr, 'warning:', msg
        if self.args.get('deprecated_sec_key'):
            # Use it and complain
            self.args['secret_key'] = self.args['deprecated_sec_key']
            msg = 'argument -s is deprecated; use -S/--secret-key instead'
            self.log.warn(msg)
            print >> sys.stderr, 'warning:', msg
        # Shell-style config file given at the CLI
        # Deprecated; should be removed in 3.2
        if os.path.isfile(self.args.get('shell_configfile', '')):
            # We already complained about this in the service
            config = _parse_shell_configfile(self.args['shell_configfile'])
            if 'EC2_ACCESS_KEY' in config and not self.args.get('key_id'):
                self.args['key_id'] = config['EC2_ACCESS_KEY']
            if 'EC2_SECRET_KEY' in config and not self.args.get('secret_key'):
                self.args['secret_key'] = config['EC2_SECRET_KEY']
        # Environment (for compatibility with AWS tools)
        if 'AWS_ACCESS_KEY' in os.environ and not self.args.get('key_id'):
            self.args['key_id'] = os.getenv('AWS_ACCESS_KEY')
        if 'AWS_SECRET_KEY' in os.environ and not self.args.get('secret_key'):
            self.args['secret_key'] = os.getenv('AWS_SECRET_KEY')
        if 'EC2_ACCESS_KEY' in os.environ and not self.args.get('key_id'):
            self.args['key_id'] = os.getenv('EC2_ACCESS_KEY')
        if 'EC2_SECRET_KEY' in os.environ and not self.args.get('secret_key'):
            self.args['secret_key'] = os.getenv('EC2_SECRET_KEY')
        # --region
        self.configure_from_configfile(only_if_explicit=True)
        # AWS credential file (location given in the environment)
        self.configure_from_aws_credential_file()
        # Regular config file
        self.configure_from_configfile()
        # User, systemwide shell-style config files
        # Deprecated; should be removed in 3.2
        for configfile_name in ('~/.eucarc', '~/.eucarc/eucarc'):
            configfile_name = os.path.expandvars(configfile_name)
            configfile_name = os.path.expanduser(configfile_name)
            if os.path.isfile(configfile_name):
                config = _parse_shell_configfile(configfile_name)
                if 'EC2_ACCESS_KEY' in config and not self.args.get('key_id'):
                    self.args['key_id'] = config['EC2_ACCESS_KEY']
                if ('EC2_SECRET_KEY' in config and
                    not self.args.get('secret_key')):
                    #
                    self.args['secret_key'] = config['EC2_SECRET_KEY']

        # That's it; make sure we have everything we need
        if not self.args.get('key_id'):
            raise AuthError('missing access key ID; please supply one with -I')
        if not self.args.get('secret_key'):
            raise AuthError('missing secret key; please supply one with -S')


class Eucalyptus(BaseService):
    NAME = 'ec2'
    DESCRIPTION = 'Eucalyptus compute cloud service'
    API_VERSION = '2013-02-01'
    AUTH_CLASS = EC2CompatibleQuerySigV2Auth
    REGION_ENVVAR = 'EUCA_REGION'
    URL_ENVVAR = 'EC2_URL'

    ARGS = [Arg('--config', dest='shell_configfile', metavar='CFGFILE',
                default='', route_to=(SERVICE, AUTH), help=argparse.SUPPRESS),
            MutuallyExclusiveArgList(
                Arg('--region', dest='userregion', metavar='USER@REGION',
                    help='''name of the region and/or user in config files to
                    use to connect to the service'''),
                Arg('-U', '--url', metavar='URL',
                    help='compute service endpoint URL'))]

    def configure(self):
        # self.args gets highest precedence for self.endpoint and user/region
        self.process_url(self.args.get('url'))
        set_userregion(self.config, self.args.get('userregion'))
        # Shell-style config file given at the CLI
        # Deprecated; should be removed in 3.2
        if os.path.isfile(self.args.get('shell_configfile', '')):
            msg = 'argument --config is deprecated'
            self.log.warn(msg)
            print >> sys.stderr, 'warning:', msg
            config = _parse_shell_configfile(self.args['shell_configfile'])
            self.process_url(config.get(self.URL_ENVVAR))
            if self.URL_ENVVAR in config:
                self.process_url(config[self.URL_ENVVAR])
        # Environment
        set_userregion(self.config, os.getenv(self.REGION_ENVVAR))
        self.process_url(os.getenv(self.URL_ENVVAR))
        # Regular config file
        self.process_url(self.config.get_region_option(self.NAME + '-url'))
        # User, systemwide shell-style config files
        # Deprecated; should be removed in 3.2
        for configfile_name in ('~/.eucarc', '~/.eucarc/eucarc'):
            configfile_name = os.path.expandvars(configfile_name)
            configfile_name = os.path.expanduser(configfile_name)
            if os.path.isfile(configfile_name):
                config = _parse_shell_configfile(configfile_name)
                if self.URL_ENVVAR in config:
                    self.process_url(config[self.URL_ENVVAR])

        # Configure request timeouts and retry handlers
        if self.max_retries is None:
            config_max_retries = self.config.get_global_option('max-retries')
            if config_max_retries is not None:
                self.max_retries = int(config_max_retries)
            else:
                self.max_retries = self.MAX_RETRIES
        if self.timeout is None:
            config_timeout = self.config.get_global_option('timeout')
            if config_timeout is not None:
                self.timeout = float(config_timeout)
            else:
                self.timeout = self.TIMEOUT

        # SSL cert verification is opt-in
        self.session_args['verify'] = self.config.get_region_option_bool(
            'verify-ssl', default=False)

        # Ensure everything is okay and finish up
        self.validate_config()
        if self.auth is not None:
            self.auth.configure()

    def handle_http_error(self, response):
        raise AWSError(response)


class EucalyptusRequest(AWSQueryRequest, TabifyingMixin):
    SUITE = Euca2ools
    SERVICE_CLASS = Eucalyptus
    METHOD = 'POST'

    def __init__(self, **kwargs):
        AWSQueryRequest.__init__(self, **kwargs)

    def print_resource_tag(self, resource_tag, resource_id):
        resource_type = RESOURCE_TYPE_MAP.lookup(resource_id)
        print self.tabify(['TAG', resource_type, resource_id,
                           resource_tag.get('key'), resource_tag.get('value')])

    def print_reservation(self, reservation):
        res_line = ['RESERVATION', reservation['reservationId'],
                    reservation.get('ownerId')]
        # group.get('entry') is a workaround for a CLC bug
        group_ids = [group.get('groupName') or group.get('groupId') or
                     group.get('entry') or ''
                     for group in reservation['groupSet']]
        res_line.append(', '.join(group_ids))
        print self.tabify(res_line)
        for instance in sorted(reservation.get('instancesSet') or [],
                               key=itemgetter('launchTime')):
            self.print_instance(instance)

    def print_instance(self, instance):
        instance_line = ['INSTANCE']
        for key in ['instanceId', 'imageId', 'dnsName', 'privateDnsName']:
            instance_line.append(instance.get(key))
        instance_line.append(instance.get('instanceState', {})
                                     .get('name'))
        instance_line.append(instance.get('keyName'))
        instance_line.append(instance.get('amiLaunchIndex'))
        instance_line.append(','.join([code['productCode'] for code in
                             instance.get('productCodes', [])]))
        instance_line.append(instance.get('instanceType'))
        instance_line.append(instance.get('launchTime'))
        instance_line.append(instance.get('placement', {}).get(
            'availabilityZone'))
        instance_line.append(instance.get('kernelId'))
        instance_line.append(instance.get('ramdiskId'))
        instance_line.append(instance.get('platform'))
        if instance.get('monitoring'):
            instance_line.append('monitoring-' +
                                 instance['monitoring'].get('state'))
        else:
            # noinspection PyTypeChecker
            instance_line.append(None)
        instance_line.append(instance.get('ipAddress'))
        instance_line.append(instance.get('privateIpAddress'))
        instance_line.append(instance.get('vpcId'))
        instance_line.append(instance.get('subnetId'))
        instance_line.append(instance.get('rootDeviceType'))
        instance_line.append(instance.get('instanceLifecycle'))
        instance_line.append(instance.get('showInstanceRequestId'))
        # noinspection PyTypeChecker
        instance_line.append(None)  # Should be the license, but where is it?
        instance_line.append(instance.get('placement', {}).get('groupName'))
        instance_line.append(instance.get('virtualizationType'))
        instance_line.append(instance.get('hypervisor'))
        instance_line.append(instance.get('clientToken'))
        instance_line.append(','.join([group['groupId'] for group in
                                       instance.get('groupSet', [])]))
        instance_line.append(instance.get('placement', {}).get('tenancy'))
        instance_line.append(instance.get('ebsOptimized'))
        instance_line.append(instance.get('iamInstanceProfile', {}).get('arn'))
        print self.tabify(instance_line)

        for blockdev in instance.get('blockDeviceMapping', []):
            self.print_blockdevice(blockdev)

        for nic in instance.get('networkInterfaceSet', []):
            self.print_interface(nic)

        for tag in instance.get('tagSet', []):
            self.print_resource_tag(tag, instance.get('instanceId'))

    def print_blockdevice(self, blockdev):
        print self.tabify(('BLOCKDEVICE', blockdev.get('deviceName'),
                           blockdev.get('ebs', {}).get('volumeId'),
                           blockdev.get('ebs', {}).get('attachTime'),
                           blockdev.get('ebs', {}).get('deleteOnTermination'),
                           blockdev.get('ebs', {}).get('volumeType'),
                           blockdev.get('ebs', {}).get('iops')))

    def print_interface(self, nic):
        nic_info = [nic.get(attr) for attr in (
            'networkInterfaceId', 'subnetId', 'vpcId', 'ownerId', 'status',
            'privateIpAddress', 'privateDnsName', 'sourceDestCheck')]
        print self.tabify(['NIC'] + nic_info)
        if nic.get('attachment'):
            attachment_info = [nic['attachment'].get(attr) for attr in (
                'attachmentID', 'deviceIndex', 'status', 'attachTime',
                'deleteOnTermination')]
            print self.tabify(['NICATTACHMENT'] + attachment_info)
        privaddresses = nic.get('privateIpAddressesSet', [])
        if nic.get('association'):
            association = nic['association']
            # The EC2 tools apparently print private IP info in the
            # association even though that info doesn't appear there
            # in the response, so we have to look it up elsewhere.
            for privaddress in privaddresses:
                if (privaddress.get('association', {}).get('publicIp') ==
                    association.get('publicIp')):
                    # Found a match
                    break
            else:
                privaddress = None
            print self.tabify(('NICASSOCIATION', association.get('publicIp'),
                               association.get('ipOwnerId'), privaddress))
        for group in nic.get('groupSet', []):
            print self.tabify(('GROUP', group.get('groupId'),
                               group.get('groupName')))
        for privaddress in privaddresses:
            print self.tabify(('PRIVATEIPADDRESS',
                               privaddress.get('privateIpAddress')))

    def print_volume(self, volume):
        vol_bits = ['VOLUME']
        for attr in ('volumeId', 'size', 'snapshotId', 'availabilityZone',
                     'status', 'createTime'):
            vol_bits.append(volume.get(attr))
        vol_bits.append(volume.get('volumeType') or 'standard')
        vol_bits.append(volume.get('iops'))
        print self.tabify(vol_bits)
        for attachment in volume.get('attachmentSet', []):
            self.print_attachment(attachment)
        for tag in volume.get('tagSet', []):
            self.print_resource_tag(tag, volume.get('volumeId'))

    def print_attachment(self, attachment):
        print self.tabify(['ATTACHMENT', attachment.get('volumeId'),
                           attachment.get('instanceId'),
                           attachment.get('device'),
                           attachment.get('status'),
                           attachment.get('attachTime')])

    def print_snapshot(self, snap):
        print self.tabify(['SNAPSHOT', snap.get('snapshotId'),
                           snap.get('volumeId'),  snap.get('status'),
                           snap.get('startTime'), snap.get('progress'),
                           snap.get('ownerId'),   snap.get('volumeSize'),
                           snap.get('description')])
        for tag in snap.get('tagSet', []):
            self.print_resource_tag(tag, snap.get('snapshotId'))

    def print_bundle_task(self, task):
        print self.tabify(['BUNDLE', task.get('bundleId'),
                           task.get('instanceId'),
                           task.get('storage', {}).get('S3', {}).get('bucket'),
                           task.get('storage', {}).get('S3', {}).get('prefix'),
                           task.get('startTime'), task.get('updateTime'),
                           task.get('state'),     task.get('progress')])


class _ResourceTypeMap(object):
    _prefix_type_map = {
        'cgw':    'customer-gateway',
        'dopt':   'dhcp-options',
        'aki':    'image',
        'ami':    'image',
        'ari':    'image',
        'eki':    'image',
        'emi':    'image',
        'eri':    'image',
        'i':      'instance',
        'igw':    'internet-gateway',
        'acl':    'network-acl',
        'xxx':    'reserved-instances',  # reserved instance IDs are UUIDs
        'rtb':    'route-table',
        'sg':     'security-group',
        'snap':   'snapshot',
        'sir':    'spot-instances-request',
        'subnet': 'subnet',
        'vol':    'volume',
        'vpc':    'vpc',
        'vpn':    'vpn-connection',
        'vgw':    'vpn-gateway'}

    def lookup(self, item):
        if not isinstance(item, basestring):
            raise TypeError('argument type must be str')
        for prefix in self._prefix_type_map:
            if item.startswith(prefix + '-'):
                return self._prefix_type_map[prefix]

    def __iter__(self):
        return iter(set(self._prefix_type_map.values()))

RESOURCE_TYPE_MAP = _ResourceTypeMap()


def _find_args_by_parg(arglike, parg):
    if isinstance(arglike, Arg):
        if parg in arglike.pargs:
            return [arglike]
        else:
            return []
    elif isinstance(arglike, list):
        matches = []
        for arg in arglike:
            matches.extend(_find_args_by_parg(arg, parg))
        return matches
    else:
        raise TypeError('Unsearchable type ' + arglike.__class__.__name__)


def _parse_shell_configfile(configfile_name):
    # Should be able to drop this in 3.2
    def sourcehook(filename):
        filename = filename.strip('"\'')
        filename = Template(filename).safe_substitute(config)
        filename = os.path.expandvars(filename)
        filename = os.path.expanduser(filename)
        return filename, open(filename)

    config = {}
    configfile_name = os.path.expandvars(configfile_name)
    configfile_name = os.path.expanduser(configfile_name)
    with open(configfile_name) as configfile:
        ## TODO:  deal with $BASH_SOURCE
        lexer = shlex.shlex(configfile)
        lexer.whitespace_split = True
        lexer.source = 'source'
        lexer.sourcehook = sourcehook
        for token in lexer:
            if '=' in token:
                (key, val) = token.split('=', 1)
                val = val.strip('"\'')
                if not config.get(key):
                    config[key] = Template(val).safe_substitute(config)
    return config
