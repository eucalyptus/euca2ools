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
import base64
import os.path
from requestbuilder import Arg, MutuallyExclusiveArgList
import sys
from . import EucalyptusRequest
from .argtypes import b64encoded_file_contents, block_device_mapping

class RunInstances(EucalyptusRequest):
    DESCRIPTION = 'Launch instances of a machine image'
    ARGS = [Arg('ImageId', metavar='IMAGE', help='image to instantiate'),
            Arg('-n', '--instance-count', dest='count', metavar='MIN[-MAX]',
                default='1', route_to=None,
                help='''number of instances to launch. If this number of
                        instances cannot be launched, no instances will launch.
                        If specified as a range (min-max), the server will
                        attempt to launch the maximum number, but no fewer
                        than the minimum number.'''),
            Arg('-g', '--group', action='append', default=[], route_to=None,
                help='security group(s) in which to launch the instances'),
            Arg('-k', '--key', dest='KeyName', metavar='KEYPAIR',
                help='name of the key pair to use'),
            MutuallyExclusiveArgList(
                Arg('-d', '--user-data', dest='UserData', metavar='DATA',
                    type=base64.b64encode,
                    help='''user data to make available to instances in this
                            reservation'''),
                Arg('--user-data-force', dest='UserData',
                    type=base64.b64encode, help=argparse.SUPPRESS),
                    # ^ deprecated  ## TODO:  decide if that should remain the case
                Arg('-f', '--user-data-file', dest='UserData',
                    metavar='DATA-FILE', type=b64encoded_file_contents,
                    help='''file containing user data to make available to the
                            instances in this reservation''')),
            Arg('--addressing', dest='AddressingType',
                choices=('public', 'private'),
                help='addressing scheme to launch the instance with'),
            Arg('-t', '--instance-type', dest='InstanceType',
                help='type of instance to launch'),
            Arg('--kernel', dest='KernelId', metavar='KERNEL',
                help='kernel to launch the instance(s) with'),
            Arg('--ramdisk', dest='RamdiskId', metavar='RAMDISK',
                help='ramdisk to launch the instance(s) with'),
            Arg('-b', '--block-device-mapping', metavar='DEVICE=MAPPED',
                dest='BlockDeviceMapping', action='append',
                type=block_device_mapping, default=[],
                help='''define a block device mapping for the instances, in the
                        form DEVICE=MAPPED, where "MAPPED" is "none",
                        "ephemeral(0-3)", or
                        "[SNAP-ID]:[SIZE]:[true|false]"'''),
            Arg('-m', '--monitor', dest='Monitoring.Enabled',
                action='store_const', const='true',
                help='enable detailed monitoring for the instance(s)'),
            Arg('--subnet', dest='SubnetId', metavar='SUBNET',
                help='VPC subnet in which to launch the instance(s)'),
            Arg('-z', '--availability-zone', metavar='ZONE',
                dest='Placement.AvailabilityZone')]
    LIST_MARKERS = ['reservationSet', 'instancesSet', 'groupSet', 'tagSet',
                    'blockDeviceMapping', 'productCodes']

    def preprocess(self):
        counts = self.args['count'].split('-')
        if len(counts) == 1:
            try:
                self.params['MinCount'] = int(counts[0])
                self.params['MaxCount'] = int(counts[0])
            except ValueError:
                self._cli_parser.error('argument -n/--instance-count: '
                                       'instance count must be an integer')
        elif len(counts) == 2:
            try:
                self.params['MinCount'] = int(counts[0])
                self.params['MaxCount'] = int(counts[1])
            except ValueError:
                self._cli_parser.error('argument -n/--instance-count: '
                        'instance count range must be must be comprised of '
                        'integers')
        else:
            self._cli_parser.error('argument -n/--instance-count: value must '
                                   'have format "1" or "1-2"')
        if self.params['MinCount'] < 1 or self.params['MaxCount'] < 1:
            self._cli_parser.error('argument -n/--instance-count: instance '
                                   'count must be positive')
        if self.params['MinCount'] > self.params['MaxCount']:
            self.log.debug('MinCount > MaxCount; swapping')
            self.params.update({'MinCount': self.params['MaxCount'],
                                'MaxCount': self.params['MinCount']})

        for group in self.args['group']:
            if group.startswith('sg-'):
                self.params.setdefault('SecurityGroupId', [])
                self.params['SecurityGroupId'].append(group)
            else:
                self.params.setdefault('SecurityGroup', [])
                self.params['SecurityGroup'].append(group)

    def print_result(self, result):
        self.print_reservation(result)
