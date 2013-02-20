# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2013, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import argparse
from euca2ools.exceptions import AWSError
from operator import itemgetter
import os.path
from requestbuilder import Arg, MutuallyExclusiveArgList, AUTH, SERVICE
from requestbuilder.auth import QuerySigV2Auth
from requestbuilder.exceptions import AuthError
from requestbuilder.mixins import TabifyingCommand
import requestbuilder.request
import requestbuilder.service
import requests
import shlex
from string import Template
import sys
from .. import Euca2ools

class EC2CompatibleQuerySigV2Auth(QuerySigV2Auth):
    # -a and -s are deprecated; remove them in 3.2
    ARGS = [Arg('-a', '--access-key', metavar='KEY_ID',
                dest='deprecated_key_id', route_to=AUTH,
                help=argparse.SUPPRESS),
            Arg('-s', metavar='KEY', dest='deprecated_sec_key', route_to=AUTH,
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
        # Shell-style config file given at the CLI
        # Deprecated; should be removed in 3.2
        if os.path.isfile(self.args['shell_configfile']):
            config = _parse_shell_configfile(self.args['shell_configfile'])
            if 'EC2_ACCESS_KEY' in config and not self.args.get('key_id'):
                self.args['key_id'] = config['EC2_ACCESS_KEY']
            if 'EC2_SECRET_KEY' in config and not self.args.get('secret_key'):
                self.args['secret_key'] = config['EC2_SECRET_KEY']
        # Environment (for compatibility with EC2 tools)
        if 'EC2_ACCESS_KEY' in os.environ and not self.args.get('key_id'):
            self.args['key_id'] = os.getenv('EC2_ACCESS_KEY')
        if 'EC2_SECRET_KEY' in os.environ and not self.args.get('secret_key'):
            self.args['secret_key'] = os.getenv('EC2_SECRET_KEY')
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
            raise AuthError('missing access key ID')
        if not self.args.get('secret_key'):
            raise AuthError('missing secret key')


class Eucalyptus(requestbuilder.service.BaseService):
    NAME = 'ec2'
    DESCRIPTION = 'Eucalyptus compute cloud service'
    API_VERSION = '2009-11-30'
    AUTH_CLASS  = EC2CompatibleQuerySigV2Auth
    URL_ENVVAR = 'EC2_URL'

    ARGS = [Arg('--config', dest='shell_configfile', metavar='CFGFILE',
                 default='', route_to=SERVICE, help=argparse.SUPPRESS),
            MutuallyExclusiveArgList(
                Arg('--region', dest='userregion', metavar='REGION',
                    route_to=SERVICE,
                    help='region name to connect to, with optional identity'),
                Arg('-U', '--url', metavar='URL', route_to=SERVICE,
                    help='compute service endpoint URL'))]

    def configure(self):
        # self.args gets highest precedence for self.endpoint and user/region
        self.process_url(self.args.get('url'))
        if self.args.get('userregion'):
            self.process_userregion(self.args['userregion'])
        # Shell-style config file given at the CLI
        # Deprecated; should be removed in 3.2
        if os.path.isfile(self.args['shell_configfile']):
            config = _parse_shell_configfile(self.args['shell_configfile'])
            self.process_url(config.get(self.URL_ENVVAR))
            if self.URL_ENVVAR in config:
                self.process_url(config[self.URL_ENVVAR])
        # Environment
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

        # Ensure everything is okay and finish up
        self.validate_config()
        if self.auth is not None:
            # HACK:  this was an easy way to make a CLI-supplied shell-style
            # config file name available to the auth handler.
            # Remove this line in 3.2.
            self.auth.args['shell_configfile'] = self.args['shell_configfile']
            self.auth.configure()

    def handle_http_error(self, response):
        raise AWSError(response)


class EucalyptusRequest(requestbuilder.request.AWSQueryRequest,
                        TabifyingCommand):
    SUITE = Euca2ools
    SERVICE_CLASS = Eucalyptus
    METHOD = 'POST'

    def __init__(self, **kwargs):
        requestbuilder.request.AWSQueryRequest.__init__(self, **kwargs)

    def parse_http_response(self, response_body):
        response = requestbuilder.request.AWSQueryRequest.parse_http_response(
            self, response_body)
        # Compute cloud controller responses enclose their useful data inside
        # FooResponse elements.  If that's all we have after stripping out
        # RequestId then just return its contents.
        useful_keys = filter(lambda x: x != 'RequestId', response.keys())
        if len(useful_keys) == 1:
            return response[useful_keys[0]]
        else:
            return response

    def print_resource_tag(self, resource_tag, resource_id):
        resource_type = RESOURCE_TYPE_MAP.lookup(resource_id)
        print self.tabify(['TAG', resource_type, resource_id,
                           resource_tag.get('key'), resource_tag.get('value')])

    def print_reservation(self, reservation):
        res_line = ['RESERVATION', reservation['reservationId'],
                    reservation.get('ownerId')]
        group_ids = [group['groupId'] for group in reservation['groupSet']]
        res_line.append(', '.join(group_ids))
        print self.tabify(res_line)
        for instance in sorted(reservation.get('instancesSet', []),
                               itemgetter('launchTime')):
            self.print_instance(instance)

    def print_instance(self, instance):
        # FIXME: Amazon's documentation doesn't say what order the fields in
        #        ec2-describe-instances output appear.
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
        instance_line.append(instance.get('placement', {}).get('availabilityZone'))
        instance_line.append(instance.get('kernelId'))
        instance_line.append(instance.get('ramdiskId'))
        instance_line.append(None)  # What is this?
        if instance.get('monitoring'):
            instance_line.append('monitoring-' +
                                 instance['monitoring'].get('state'))
        else:
            instance_line.append(None)
        instance_line.append(instance.get('ipAddress'))
        instance_line.append(instance.get('privateIpAddress'))
        instance_line.append(instance.get('vpcId'))
        instance_line.append(instance.get('subnetId'))
        instance_line.append(instance.get('rootDeviceType'))
        instance_line.append(None)  # What is this?
        instance_line.append(None)  # What is this?
        instance_line.append(None)  # What is this?
        instance_line.append(None)  # What is this?
        instance_line.append(instance.get('virtualizationType'))
        instance_line.append(instance.get('hypervisor'))
        instance_line.append(None)  # What is this?
        instance_line.append(instance.get('placement', {}).get('groupName'))
        instance_line.append(','.join([group['groupId'] for group in
                                       instance.get('groupSet', [])]))
        instance_line.append(instance.get('placement', {}).get('tenancy'))
        print self.tabify(instance_line)

        for blockdev in instance.get('blockDeviceMapping', []):
            self.print_blockdevice(blockdev)

        for tag in instance.get('tagSet', []):
            self.print_resource_tag(tag, instance.get('instanceId'))

    def print_blockdevice(self, blockdev):
        print self.tabify(['BLOCKDEVICE', blockdev.get('deviceName'),
                           blockdev.get('ebs', {}).get('volumeId'),
                           blockdev.get('ebs', {}).get('attachTime'),
                           blockdev.get('ebs', {}).get('deleteOnTermination')])

    def print_volume(self, volume):
        print self.tabify(['VOLUME'] + [volume.get(attr) for attr in
                ('volumeId', 'size', 'snapshotId', 'availabilityZone',
                 'status', 'createTime')])
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
            'XXX':    'reserved-instances',  # reserved instance IDs are UUIDs
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
        return (filename, open(filename))

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
