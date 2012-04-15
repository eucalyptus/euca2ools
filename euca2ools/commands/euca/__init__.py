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
import os.path
from requestbuilder import Arg, CONNECTION
from requestbuilder.mixins import TabifyingCommand
import requestbuilder.service
import shlex
from string import Template
from .. import Euca2oolsRequest

class Eucalyptus(requestbuilder.service.BaseService):
    Description = 'Eucalyptus compute cloud controller'
    APIVersion = '2009-11-30'
    EnvURL = 'EC2_URL'

    def __init__(self, configfile=None, **kwargs):
        self.configfile_name = configfile
        requestbuilder.service.BaseService.__init__(self, **kwargs)

    def find_credentials(self):
        # CLI-given env-style config file
        if os.path.isfile(self.configfile_name or ''):
            config = _parse_configfile(self.configfile_name)
            self._populate_init_args_from_env_config(config)
        # AWS credential file (path is in the environment)
        requestbuilder.service.BaseService.find_credentials(self)
        # Environment
        config = self._get_env_config_from_env()
        self._populate_init_args_from_env_config(config)
        # User, systemwide env-style config files
        for configfile_name in (self.configfile_name or '',
                                '~/.eucarc', '~/.eucarc/eucarc'):
            configfile_name = os.path.expandvars(configfile_name)
            configfile_name = os.path.expanduser(configfile_name)
            if os.path.isfile(configfile_name):
                config = _parse_configfile(configfile_name)
                self._populate_init_args_from_env_config(config)

    _init_args_key_map = {'EC2_ACCESS_KEY':   'aws_access_key_id',
                          'EC2_SECRET_KEY':   'aws_secret_access_key',
                          'EC2_URL':          'url'}

    def _get_env_config_from_env(self):
        envconfig = {}
        for key in self._init_args_key_map:
            if key in os.environ:
                envconfig[key] = os.getenv(key)
        return envconfig

    def _populate_init_args_from_env_config(self, envconfig):
        '''
        Populate self._init_args from the contents of an environment
        variable-like dict.
        '''
        for (env_key, initargs_key) in self._init_args_key_map.iteritems():
            if env_key in envconfig and not self._init_args.get(initargs_key):
                self._init_args[initargs_key] = envconfig[env_key]

def _parse_configfile(configfile_name):
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

## TODO:  regions
class EucalyptusRequest(Euca2oolsRequest, TabifyingCommand):
    ServiceClass = Eucalyptus

    Args = [Arg('-I', '-a', '--access-key-id', '--access-key',
                metavar='KEY_ID', dest='aws_access_key_id',
                route_to=CONNECTION),
            Arg('-S', '-s', '--secret-key', metavar='KEY',
                dest='aws_secret_access_key', route_to=CONNECTION),
            Arg('-U', '--url', route_to=CONNECTION,
                help='cloud controller URL'),
            Arg('--config', dest='configfile', metavar='CFGFILE',
                 route_to=CONNECTION)]

    def __init__(self, **kwargs):
        # If an inheriting class defines '-a' or '-s' args, resolve conflicts
        # with this class's old-style auth args by capitalizing this class's
        # auth args.
        a_args = _find_args_by_parg(self.Args, '-a')
        s_args = _find_args_by_parg(self.Args, '-s')
        if len(a_args) > 1 or len(s_args) > 1:
            for arg in a_args:
                if '--access-key' in arg.pargs:
                    arg.pargs = tuple('-A' if parg == '-a' else parg
                                      for parg in arg.pargs)
            for arg in s_args:
                if '--secret-key' in arg.pargs:
                    arg.pargs = tuple(parg for parg in arg.pargs
                                      if parg != '-s')
        Euca2oolsRequest.__init__(self, **kwargs)

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
        instance_line.append(instance.get('placement', {}).get('availabilityZone'))
        instance_line.append(instance.get('kernelId'))
        instance_line.append(instance.get('ramdiskId'))
        if instance.get('monitoring'):
            instance_line.append('monitoring-' +
                                 instance['monitoring'].get('state'))
        else:
            instance_line.append(None)
        instance_line.append(instance.get('ipAddress'))
        instance_line.append(instance.get('privateIpAddress'))
        instance_line.append(instance.get('rootDeviceType'))
        instance_line.append(instance.get('virtualizationType'))
        instance_line.append(instance.get('hypervisor'))
        instance_line.append(instance.get('subnetId'))
        instance_line.append(instance.get('vpcId'))
        instance_line.append(instance.get('placement', {}).get('groupName'))
        instance_line.append(','.join([group['groupId'] for group in
                                       instance.get('groupSet', [])]))
        instance_line.append(instance.get('placement', {}).get('tenancy'))
        print self.tabify(instance_line)

        for blockdev in instance.get('blockDeviceMapping', []):
            self.print_blockdevice(blockdev)

        for tag in instance.get('tagSet', []):
            print self.tabify(['TAG', 'instance', instance.get('instanceId'),
                               tag.get('key'), tag.get('value')])

    def print_blockdevice(self, blockdev):
        print self.tabify(['BLOCKDEVICE', blockdev.get('deviceName'),
                           blockdev.get('ebs', {}).get('volumeId'),
                           blockdev.get('ebs', {}).get('attachTime'),
                           blockdev.get('ebs', {}).get('deleteOnTermination')])

    def print_volume(self, volume):
        print 'VOLUME', self.tabify([volume.get(attr) for attr in
                ('volumeId', 'size', 'snapshotId', 'availabilityZone',
                 'status', 'createTime')])
        for attachment in volume.get('attachmentSet', []):
            print 'ATTACHMENT', self.tabify([volume.get('volumeId')] +
                    [attachment.get(attr) for attr in
                     ('instanceId', 'device', 'status', 'attachTime')])

## TODO:  test this
class BlockDeviceMapping(dict):
    '''
    A block device mapping as given on the image registration command line
    '''
    def __init__(self, map_as_str):
        dict.__init__(self)
        try:
            (device, mapping) = map_as_str.split('=')
        except ValueError:
            raise argparse.ArgumentTypeError('block device mapping {0} must '
                    'have form KEY=VALUE'.format(map_as_str))
            if mapping.lower() == 'none':
                ## FIXME:  NoDevice should be an empty element
                self['Ebs'] = {'NoDevice': 'true'}
            elif mapping.startswith('ephemeral'):
                self['VirtualName'] = mapping
            elif (mapping.startswith('snap-') or mapping.startswith('vol-') or
                  mapping.startswith(':')):
                map_bits = mapping.split(':')
                if len(map_bits) == 1:
                    map_bits.append(None)
                if len(map_bits) == 2:
                    map_bits.append('true')
                if len(map_bits) != 3:
                    raise argparse.ArgumentTypeError(
                            'EBS block device mapping {0} must have form '
                            '[snap-id]:[size]:[true|false]'.format(map_as_str))
                try:
                    int(map_bits[1])
                except TypeError:
                    raise argparse.ArgumentTypeError(
                            'second element of EBS block device mapping {0} '
                            'must be an integer')
                if map_bits[2] not in ('true', 'false'):
                    raise argparse.ArgumentTypeError(
                            'third element of EBS block device mapping {0} '
                            "must be 'true' or 'false'".format(map_as_str))
                self['Ebs'] = {'SnapshotId':          map_bits[0],
                               'VolumeSize':          map_bits[1],
                               'DeleteOnTermination': map_bits[2]}

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
