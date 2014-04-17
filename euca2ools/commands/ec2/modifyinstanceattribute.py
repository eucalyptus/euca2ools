# Copyright 2009-2014 Eucalyptus Systems, Inc.
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

import base64
import os.path

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.argtypes import ec2_block_device_mapping
from euca2ools.commands.ec2 import EC2Request


class ModifyInstanceAttribute(EC2Request):
    DESCRIPTION = 'Modify an attribute of an instance'
    ARGS = [Arg('InstanceId', metavar='INSTANCE', help='instance to modify'),
            MutuallyExclusiveArgList(
                Arg('-b', '--block-device-mapping', metavar='DEVICE=MAPPED',
                    dest='BlockDeviceMapping', action='append',
                    type=ec2_block_device_mapping, default=[],
                    help='''define a block device mapping for the instances, in the
                    form DEVICE=MAPPED, where "MAPPED" is "none", "ephemeral(0-3)",
                    or
                    "[SNAP-ID]:[GiB]:[true|false]:[standard|VOLTYPE[:IOPS]]"'''),
                Arg('--disable-api-termination', dest='DisableApiTermination',
                    action='store_true', route_to=None,
                    help='prevent API users from terminating the instance(s)'),
                Arg('--instance-initiated-shutdown-behavior',
                    dest='InstanceInitiatedShutdownBehavior',
                    choices=('stop', 'terminate'),
                    help=('whether to "stop" (default) or terminate EBS instances '
                          'when they shut down')),
                Arg('--ebs-optimized', dest='EbsOptimized', action='store_const',
                    const='true', help='optimize the new instance(s) for EBS I/O'),
                Arg('-g', '--group', action='append', default=[], route_to=None,
                    help='security group(s) in which to launch the instances'),
                Arg('-t', '--instance-type', metavar='ENTITY', action='append', default=[],
                    route_to=None, help='''the type of the instance'''),
                Arg('--kernel', metavar='ENTITY', action='append',
                    default=[], route_to=None, help='''the ID of the kernel'''),
                Arg('--ramdisk', metavar='ENTITY', action='append',
                    default=[], route_to=None, help='''the ID of the ramdisk'''),
                Arg('-d', '--user-data', metavar='DATA', route_to=None,
                    help='''user data to make available to instances in this
                            reservation'''),
                Arg('--user-data-force', metavar='DATA', route_to=None,
                    help='''same as -d/--user-data, but without checking if a
                    file by that name exists first'''),
                Arg('-f', '--user-data-file', metavar='FILE', route_to=None,
                    help='''file containing user data to make available to the
                    instances in this reservation'''))
    ]
    # still missing: source-dest-check, sriov

    # noinspection PyExceptionInherit
    def configure(self):
        EC2Request.configure(self)
        if self.args.get('user_data'):
            if os.path.isfile(self.args['user_data']):
                raise ArgumentError(
                    'argument -d/--user-data: to pass the contents of a file '
                    'as user data, use -f/--user-data-file.  To pass the '
                    "literal value '{0}' as user data even though it matches "
                    'the name of a file, use --user-data-force.')
            else:
                self.params['UserData'] = base64.b64encode(
                    self.args['user_data'])
        elif self.args.get('user_data_force'):
            self.params['UserData'] = base64.b64encode(
                self.args['user_data_force'])
        elif self.args.get('user_data_file'):
            with open(self.args['user_data_file']) as user_data_file:
                self.params['UserData'] = base64.b64encode(
                    user_data_file.read())

    # noinspection PyExceptionInherit
    def preprocess(self):
        for group in self.args['group']:
            if group.startswith('sg-'):
                self.params.setdefault('SecurityGroupId', [])
                self.params['SecurityGroupId'].append(group)
            else:
                self.params.setdefault('SecurityGroup', [])
                self.params['SecurityGroup'].append(group)
        if self.args.get('disable_api_termination'):
            self.params['DisableApiTermination.Value'].append(self.args.get('disable_api_termination'))


    def print_result(self, _):
        print "yay, it worked!"
