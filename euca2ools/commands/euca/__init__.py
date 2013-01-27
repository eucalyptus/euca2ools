# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2012, Eucalyptus Systems, Inc.
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
from operator import itemgetter
import os.path
from requestbuilder import Arg, MutuallyExclusiveArgList, AUTH, SERVICE, \
        STD_AUTH_ARGS
from requestbuilder.mixins import TabifyingCommand
import requestbuilder.service
import shlex
from string import Template
import sys
from .. import Euca2oolsRequest

class Eucalyptus(requestbuilder.service.BaseService):
    Name = 'ec2'
    DESCRIPTION = 'Eucalyptus compute cloud service'
    API_VERSION = '2009-11-30'
    EnvURL = 'EC2_URL'

    def __init__(self, config, log, shell_configfile=None,
                 deprecated_key_id=None, deprecated_sec_key=None,
                 auth_args=None, **kwargs):
        self.shell_configfile_name = shell_configfile
        if deprecated_key_id and not auth_args.get('key_id'):
            auth_args['key_id'] = deprecated_key_id
            msg = 'given access key ID argument is deprecated; use -I instead'
            log.warn(msg)
            print >> sys.stderr, 'warning:', msg
        if deprecated_sec_key and not auth_args.get('secret_key'):
            auth_args['secret_key'] = deprecated_sec_key
            msg = 'argument -s is deprecated; use -S instead'
            log.warn(msg)
            print >> sys.stderr, 'warning:', msg
        requestbuilder.service.BaseService.__init__(self, config, log,
                                                    auth_args=auth_args,
                                                    **kwargs)

    def read_config(self):
        # CLI-given shell-style config file
        if os.path.isfile(self.shell_configfile_name or ''):
            config = _parse_shell_configfile(self.shell_configfile_name)
            self._populate_self_from_env_config(config)
        # AWS credential file (path is in the environment)
        self.read_aws_credential_file()
        # Environment
        config = self._get_env_config_from_env()
        self._populate_self_from_env_config(config)
        # Requestbuilder config files
        self.read_requestbuilder_config()
        # User, systemwide shell-style config files
        for configfile_name in ('~/.eucarc', '~/.eucarc/eucarc'):
            configfile_name = os.path.expandvars(configfile_name)
            configfile_name = os.path.expanduser(configfile_name)
            if os.path.isfile(configfile_name):
                config = _parse_shell_configfile(configfile_name)
                self._populate_self_from_env_config(config)

    def _get_env_config_from_env(self):
        envconfig = {}
        for key in ('EC2_ACCESS_KEY', 'EC2_SECRET_KEY', 'EC2_URL'):
            if key in os.environ:
                envconfig[key] = os.getenv(key)
        return envconfig

    def _populate_self_from_env_config(self, envconfig):
        '''
        Populate this service from the contents of an environment
        variable-like dict.
        '''
        for (env_key, val) in envconfig.iteritems():
            if (env_key == 'EC2_ACCESS_KEY' and
                not self._auth_args.get('key_id')):
                self._auth_args['key_id'] = val
            elif (env_key == 'EC2_SECRET_KEY' and
                  not self._auth_args.get('secret_key')):
                self._auth_args['secret_key'] = val
            elif env_key == 'EC2_URL' and not self.endpoint_url:
                self._set_url_vars(val)

def _parse_shell_configfile(configfile_name):
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

class EucalyptusRequest(Euca2oolsRequest, TabifyingCommand):
    ServiceClass = Eucalyptus

    # For compatibility with euca2ools versions earlier than 3, we include the
    # old -a/--access-key/-s args.  As before, if either -a or -s conflicts
    # with another arg, both are capitalized.  All are deprecated.  They are no
    # longer documented and using them will result in warnings.
    ARGS = [Arg('-a', '--access-key', metavar='KEY_ID',
                dest='deprecated_key_id', route_to=SERVICE,
                help=argparse.SUPPRESS),
            Arg('-s', metavar='KEY', dest='deprecated_sec_key',
                route_to=SERVICE, help=argparse.SUPPRESS),
            Arg('--config', dest='shell_configfile', metavar='CFGFILE',
                 route_to=SERVICE, help=argparse.SUPPRESS),
            MutuallyExclusiveArgList(
                Arg('--region', dest='regionspec', metavar='REGION',
                    route_to=SERVICE,
                    help='region name to connect to, with optional identity'),
                Arg('-U', '--url', metavar='URL', route_to=SERVICE,
                    help='compute service endpoint URL'))] + STD_AUTH_ARGS

    def __init__(self, **kwargs):
        # If an inheriting class defines '-a' or '-s' args, resolve conflicts
        # with this class's old-style auth args by capitalizing this class's
        # auth args.
        args = self.aggregate_subclass_fields('ARGS')
        a_args = _find_args_by_parg(args, '-a')
        s_args = _find_args_by_parg(args, '-s')
        if len(a_args) > 1 or len(s_args) > 1:
            for arg in a_args:
                if arg.kwargs.get('dest') == 'deprecated_key_id':
                    arg.pargs = tuple('-A' if parg == '-a' else parg
                                      for parg in arg.pargs)
            for arg in s_args:
                if arg.kwargs.get('dest') == 'deprecated_sec_key':
                    arg.kwargs['dest'] = argparse.SUPPRESS
        Euca2oolsRequest.__init__(self, **kwargs)
        self.method = 'POST'  ## FIXME

    def parse_http_response(self, response_body):
        response = Euca2oolsRequest.parse_http_response(self, response_body)
        # Compute cloud controller responses enclose their useful data inside
        # FooResponse # elements.  If that's all we have after stripping out
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
        ## FIXME: Amazon's documentation doesn't say what order the fields in
        ##        ec2-describe-instances output appear.
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
