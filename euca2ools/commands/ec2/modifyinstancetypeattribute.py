# Copyright 2013-2014 Eucalyptus Systems, Inc.
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

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import TabifyingMixin

from euca2ools.commands.ec2 import EC2Request


class ModifyInstanceTypeAttribute(EC2Request, TabifyingMixin):
    DESCRIPTION = '[Eucalyptus cloud admin only] Modify an instance type'
    ARGS = [Arg('Name', metavar='INSTANCETYPE',
                help='name of the instance type to modify (required)'),
            Arg('-c', '--cpus', dest='Cpu', metavar='COUNT', type=int,
                help='number of virtual CPUs to allocate to each instance'),
            Arg('-d', '--disk', dest='Disk', metavar='GiB', type=int,
                help='amount of instance storage to allow each instance'),
            Arg('-m', '--memory', dest='Memory', metavar='MiB', type=int,
                help='amount of RAM to allocate to each instance'),
            Arg('--reset', dest='Reset', action='store_true',
                help='reset the instance type to its default configuration')]

    # noinspection PyExceptionInherit
    def configure(self):
        EC2Request.configure(self)
        if (self.args.get('Reset') and
            any(self.args.get(attr) is not None for attr in ('Cpu', 'Disk',
                                                             'Memory'))):
            # Basically, reset is mutually exclusive with everything else.
            raise ArgumentError('argument --reset may not be used with '
                                'instance type attributes')

    def print_result(self, result):
        newtype = result.get('instanceType', {})
        print self.tabify(('INSTANCETYPE', newtype.get('name'),
                           newtype.get('cpu'), newtype.get('memory'),
                           newtype.get('disk')))
