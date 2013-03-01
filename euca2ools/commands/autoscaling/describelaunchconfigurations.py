# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
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

from euca2ools.commands.autoscaling import AutoScalingRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingCommand
from requestbuilder.response import PaginatedResponse

class DescribeLaunchConfigurations(AutoScalingRequest, TabifyingCommand):
    DESCRIPTION = 'Describe auto-scaling instance launch configurations'
    ARGS = [Arg('LaunchConfigurationNames.member', metavar='LAUNCHCONFIG',
                nargs='*',
                help='limit results to specific launch configurations'),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the launch configurations' info")]
    LIST_MARKERS = ['LaunchConfigurations', 'SecurityGroups',
                    'BlockDeviceMappings']

    def main(self):
        return PaginatedResponse(self, (None,), ('LaunchConfigurations',))

    def prepare_for_page(self, page):
        # Pages are defined by NextToken
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        for config in result.get('LaunchConfigurations', []):
            bits = ['LAUNCH-CONFIG']
            bits.append(config.get('LaunchConfigurationName'))
            bits.append(config.get('ImageId'))
            bits.append(config.get('InstanceType'))
            if self.args['show_long']:
                bits.append(config.get('KeyName'))
                bits.append(config.get('KernelId'))
                bits.append(config.get('RamdiskId'))
                block_maps = [convert_block_mapping_to_str(mapping) for mapping
                              in config.get('BlockDeviceMappings', [])]
                if len(block_maps) > 0:
                    bits.append('{' + ','.join(block_maps) + '}')
                else:
                    bits.append(None)
                bits.append(','.join(config.get('SecurityGroups', [])) or None)
                bits.append(config.get('CreatedTime'))
                bits.append(config.get('InstanceMonitoring', {}).get('Enabled'))
                bits.append(config.get('LaunchConfigurationARN'))
            bits.append(config.get('SpotPrice'))
            bits.append(config.get('IamInstanceProfile'))
            if self.args['show_long']:
                bits.append(config.get('EbsOptimized'))
            print self.tabify(bits)


def convert_block_mapping_to_str(mapping):
    if mapping.get('Ebs'):
        mapped = ':'.join((mapping['Ebs'].get('SnapshotId') or '',
                           mapping['Ebs'].get('VolumeSize') or ''))
    elif mapping.get('VirtualName'):
        mapped = mapping['VirtualName']
    else:
        raise ValueError('unexpected block device mapping: {0}'.format(mapping))
    return mapping['DeviceName'] + '=' + mapped
