# Copyright 2014 Eucalyptus Systems, Inc.
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

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.argtypes import flexible_bool
from euca2ools.commands.ec2 import EC2Request


class ModifyNetworkInterfaceAttribute(EC2Request):
    DESCRIPTION = 'Modify an attribute of a VPC network interface'
    ARGS = [Arg('NetworkInterfaceId', metavar='INTERFACE',
                help='ID of the network interface to modify (required)'),
            MutuallyExclusiveArgList(
                Arg('-d', '--description', dest='Description.Value',
                    metavar='DESC',
                    help="set the interface's description"),
                Arg('--source-dest-check', dest='SourceDestCheck.Value',
                    type=flexible_bool, metavar='(true|false)',
                    help='set whether source/destination checking is enabled'),
                Arg('--group-id', dest='SecurityGroupId', action='append',
                    metavar='GROUP', help='''set the security groups the
                    network interface belongs to (use more than one to
                    specify multiple groups)'''),
                Arg('-a', '--attachment', dest='Attachment.AttachmentId',
                    metavar='ATTACHMENT', help='''the ID of an attachment to
                    modify.  --delete-on-termination is required when this
                    option is used.'''))
            .required(),
            Arg('--delete-on-termination', metavar='(true|false)',
                type=flexible_bool, dest='Attachment.DeleteOnTermination',
                help='''set whether the interface's attachment will be
                deleted when the instance terminates (requires
                -a/--attachment)''')]

    def configure(self):
        EC2Request.configure(self)
        if (self.args.get('Attachment.DeleteOnTermination') is not None and
                not self.args.get('Attachment.AttachmentId')):
            raise ArgumentError('argument --delete-on-termination may only be '
                                'used with -a/--attachment')
        if (self.args.get('Attachment.AttachmentId') and
                self.args.get('Attachment.DeleteOnTermination') is None):
            raise ArgumentError('argument -a/--attachment also requires '
                                '--delete-on-termination')
