# Copyright (c) 2009-2016 Hewlett Packard Enterprise Development LP
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

from euca2ools.commands.argtypes import (ec2_block_device_mapping,
                                         flexible_bool, vpc_interface)
from euca2ools.commands.ec2 import EC2Request


class RunInstances(EC2Request):
    DESCRIPTION = 'Launch instances of a machine image'
    ARGS = [Arg('ImageId', metavar='IMAGE',
                help='ID of the image to instantiate (required)'),
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
                Arg('-d', '--user-data', metavar='DATA', route_to=None,
                    help='''user data to make available to instances in this
                            reservation'''),
                Arg('--user-data-force', metavar='DATA', route_to=None,
                    help='''same as -d/--user-data, but without checking if a
                    file by that name exists first'''),
                Arg('-f', '--user-data-file', metavar='FILE', route_to=None,
                    help='''file containing user data to make available to the
                    instances in this reservation''')),
            Arg('--addressing', dest='AddressingType',
                choices=('public', 'private'),
                help='''[Eucalyptus only, non-VPC only]
                addressing scheme to launch the instance with.  Use "private"
                to run an instance with no public address.'''),
            Arg('-t', '--instance-type', dest='InstanceType',
                help='type of instance to launch'),
            Arg('-z', '--availability-zone', metavar='ZONE',
                dest='Placement.AvailabilityZone'),
            Arg('--kernel', dest='KernelId', metavar='KERNEL',
                help='ID of the kernel to launch the instance(s) with'),
            Arg('--ramdisk', dest='RamdiskId', metavar='RAMDISK',
                help='ID of the ramdisk to launch the instance(s) with'),
            Arg('-b', '--block-device-mapping', metavar='DEVICE=MAPPED',
                dest='BlockDeviceMapping', action='append',
                type=ec2_block_device_mapping, default=[],
                help='''define a block device mapping for the instances, in the
                form DEVICE=MAPPED, where "MAPPED" is "none", "ephemeral(0-3)",
                or
                "[SNAP-ID]:[GiB]:[true|false]:[standard|VOLTYPE[:IOPS]]"'''),
            Arg('-m', '--monitor', dest='Monitoring.Enabled',
                action='store_const', const='true',
                help='enable detailed monitoring for the instance(s)'),
            Arg('--disable-api-termination', dest='DisableApiTermination',
                action='store_const', const='true',
                help='prevent API users from terminating the instance(s)'),
            Arg('--instance-initiated-shutdown-behavior',
                dest='InstanceInitiatedShutdownBehavior',
                choices=('stop', 'terminate'),
                help=('whether to "stop" (default) or terminate EBS instances '
                      'when they shut down')),
            Arg('--placement-group', dest='Placement.GroupName',
                metavar='PLGROUP', help='''name of a placement group to launch
                into'''),
            Arg('--tenancy', dest='Placement.Tenancy',
                choices=('default', 'dedicated'), help='''[VPC only]
                "dedicated" to run on single-tenant hardware'''),
            Arg('--client-token', dest='ClientToken', metavar='TOKEN',
                help='unique identifier to ensure request idempotency'),
            Arg('-s', '--subnet', metavar='SUBNET', route_to=None,
                help='''[VPC only] subnet to create the instance's network
                interface in'''),
            Arg('--associate-public-ip-address', type=flexible_bool,
                route_to=None, help='''[VPC only] whether or not to assign a
                public address to the instance's network interface'''),
            Arg('--private-ip-address', metavar='ADDRESS', route_to=None,
                help='''[VPC only] assign a specific primary private IP address
                to an instance's interface'''),
            MutuallyExclusiveArgList(
                Arg('--secondary-address', '--secondary-private-ip-address',
                    metavar='ADDRESS', action='append', route_to=None,
                    help='''[VPC only] assign a specific secondary private IP
                    address to an instance's network interface.  Use this
                    option multiple times to add additional addresses.'''),
                Arg('--secondary-count', '--secondary-private-ip-address-count',
                    metavar='COUNT', type=int, route_to=None, help='''[VPC only]
                    automatically assign a specific number of secondary private
                    IP addresses to an instance's network interface''')),
            Arg('-a', '--network-interface', dest='NetworkInterface',
                metavar='INTERFACE', action='append', type=vpc_interface,
                help=('[VPC only] add a network interface to the new '
                      'instance.  If the interface already exists, supply its '
                      'ID and a numeric index for it, separated by ":", in '
                      'the form "eni-NNNNNNNN:INDEX".  To create a new '
                      'interface, supply a numeric index and subnet ID for '
                      'it, along with (in order) an optional description, a '
                      'primary private IP address, a list of security group '
                      'IDs to associate with the interface, whether to delete '
                      'the interface upon instance termination ("true" or '
                      '"false"), a number of secondary private IP addresses '
                      'to create automatically, and a list of secondary '
                      'private IP addresses to assign to the interface, '
                      'separated by ":", in the form ":INDEX:SUBNET:'
                      '[DESCRIPTION]:[PRIV_IP]:[GROUP1,GROUP2,...]:[true|'
                      'false]:[SEC_IP_COUNT|:SEC_IP1,SEC_IP2,...]".  You '
                      'cannot specify both of the latter two.  This option '
                      'may be used multiple times.  Each adds another network '
                      'interface.')),
            Arg('-p', '--iam-profile', metavar='IPROFILE', route_to=None,
                help='''name or ARN of the IAM instance profile to associate
                with the new instance(s)'''),
            Arg('--ebs-optimized', dest='EbsOptimized', action='store_const',
                const='true', help='optimize the new instance(s) for EBS I/O')]

    LIST_TAGS = ['reservationSet', 'instancesSet', 'groupSet', 'tagSet',
                 'blockDeviceMapping', 'productCodes', 'networkInterfaceSet',
                 'privateIpAddressesSet']

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

        if self.args.get('KeyName') is None:
            default_key_name = self.config.get_region_option(
                'ec2-default-keypair')
            if default_key_name:
                self.log.info("using default key pair '%s'", default_key_name)
                self.params['KeyName'] = default_key_name

    # noinspection PyExceptionInherit
    def preprocess(self):
        counts = self.args['count'].split('-')
        if len(counts) == 1:
            try:
                self.params['MinCount'] = int(counts[0])
                self.params['MaxCount'] = int(counts[0])
            except ValueError:
                raise ArgumentError('argument -n/--instance-count: instance '
                                    'count must be an integer')
        elif len(counts) == 2:
            try:
                self.params['MinCount'] = int(counts[0])
                self.params['MaxCount'] = int(counts[1])
            except ValueError:
                raise ArgumentError('argument -n/--instance-count: instance '
                                    'count range must be must be comprised of '
                                    'integers')
        else:
            raise ArgumentError('argument -n/--instance-count: value must '
                                'have format "1" or "1-2"')
        if self.params['MinCount'] < 1 or self.params['MaxCount'] < 1:
            raise ArgumentError('argument -n/--instance-count: instance count '
                                'must be positive')
        if self.params['MinCount'] > self.params['MaxCount']:
            self.log.debug('MinCount > MaxCount; swapping')
            self.params.update({'MinCount': self.params['MaxCount'],
                                'MaxCount': self.params['MinCount']})

        iprofile = self.args.get('iam_profile')
        if iprofile:
            if iprofile.startswith('arn:'):
                self.params['IamInstanceProfile.Arn'] = iprofile
            else:
                self.params['IamInstanceProfile.Name'] = iprofile

        if (self.args.get('subnet') or self.args.get('NetworkInterface') or
                self.args.get('associate_public_ip_address') is not None):
            # This is going into a VPC.
            # We can't mix top-level and interface-level parameters, so
            # build an interface out of all the network-related options
            # to make the split-up, "friendlier" options work.
            cli_iface = {}
            for group in self.args['group']:
                if not group.startswith('sg-'):
                    raise ArgumentError('argument -g/--group: groups must be '
                                        'specified by ID when using VPC')
                cli_iface.setdefault('SecurityGroupId', [])
                cli_iface['SecurityGroupId'].append(group)
            if self.args.get('associate_public_ip_address') is not None:
                cli_iface['AssociatePublicIpAddress'] = \
                    self.args['associate_public_ip_address']
            if self.args.get('private_ip_address'):
                cli_iface['PrivateIpAddresses'] = [
                    {'PrivateIpAddress': self.args['private_ip_address'],
                     'Primary': 'true'}]
            if self.args.get('secondary_address'):
                sec_ips = [{'PrivateIpAddress': addr} for addr in
                           self.args['secondary_address']]
                if not cli_iface.get('PrivateIpAddresses'):
                    cli_iface['PrivateIpAddresses'] = []
                cli_iface['PrivateIpAddresses'].extend(sec_ips)
            if self.args.get('secondary_count'):
                sec_ip_count = self.args['secondary_count']
                cli_iface['SecondaryPrivateIpAddressCount'] = sec_ip_count
            if self.args.get('subnet'):
                cli_iface['SubnetId'] = self.args['subnet']
            if cli_iface:
                cli_iface['DeviceIndex'] = 0
                if not self.params.get('NetworkInterface'):
                    self.params['NetworkInterface'] = []
                self.params['NetworkInterface'].append(cli_iface)
            self.log.debug('built network interface from CLI options: {0}'
                           .format(cli_iface))
        else:
            # Non-VPC
            for group in self.args['group']:
                if group.startswith('sg-'):
                    if not self.params.get('SecurityGroupId'):
                        self.params['SecurityGroupId'] = []
                    self.params['SecurityGroupId'].append(group)
                else:
                    if not self.params.get('SecurityGroup'):
                        self.params['SecurityGroup'] = []
                    self.params['SecurityGroup'].append(group)


    def print_result(self, result):
        self.print_reservation(result)
