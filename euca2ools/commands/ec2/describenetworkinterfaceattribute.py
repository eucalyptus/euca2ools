# Copyright (c) 2014-2016 Hewlett Packard Enterprise Development LP
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

from euca2ools.commands.ec2 import EC2Request


class DescribeNetworkInterfaceAttribute(EC2Request):
    DESCRIPTION = 'Show an attribute of a VPC network interface'
    ARGS = [Arg('NetworkInterfaceId', metavar='INTERFACE', help='''ID of the
                network interface to show info for (required)'''),
            MutuallyExclusiveArgList(
                Arg('-d', '--description', dest='Attribute',
                    action='store_const', const='description',
                    help="show the interface's description"),
                Arg('--source-dest-check', dest='Attribute',
                    action='store_const', const='sourceDestCheck',
                    help='''show whether source/destination address
                    checking is enabled'''),
                Arg('--group-set', dest='Attribute', action='store_const',
                    const='groupSet', help='''show the security groups the
                    network interface belongs to'''),
                Arg('-a', '--attachment', dest='Attribute',
                    action='store_const', const='attachment', help='''show info
                    about the interface's attachment (if any)'''))
            .required()]

    LIST_TAGS = ['groupSet']

    def print_result(self, result):
        print self.tabify(('NETWORKINTERFACE',
                           result.get('networkInterfaceId'),
                           self.args['Attribute']))
        if self.args['Attribute'] == 'description':
            print self.tabify(('DESCRIPTION',
                               result['description'].get('value')))
        elif self.args['Attribute'] == 'sourceDestCheck':
            print self.tabify(('SOURCEDESTCHECK',
                               result['sourceDestCheck'].get('value')))
        elif self.args['Attribute'] == 'groupSet':
            for group in result.get('groupSet') or []:
                print self.tabify(('GROUP', group.get('groupId'),
                                   group.get('groupName')))
        elif self.args['Attribute'] == 'attachment':
            attachment = result.get('attachment')
            if attachment:
                attachment_info = [attachment.get(attr) for attr in (
                    'attachmentID', 'deviceIndex', 'status', 'attachTime',
                    'deleteOnTermination')]
                print self.tabify(['ATTACHMENT'] + attachment_info)
