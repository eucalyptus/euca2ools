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

from euca2ools.commands.ec2 import EC2Request


class DescribeVpcAttribute(EC2Request):
    DESCRIPTION = 'Show an attribute of a VPC'
    ARGS = [Arg('VpcId', metavar='VPC',
                help='ID of the VPC to show info for (required)'),
            MutuallyExclusiveArgList(
                Arg('-d', '--dns-hostnames', dest='Attribute',
                    action='store_const', const='enableDnsHostnames',
                    help='''show whether instances in the VPC are
                    assigned DNS hostnames'''),
                Arg('-s', '--dns-support', dest='Attribute',
                    action='store_const', const='enableDnsSupport',
                    help='show whether DNS resolution is enabled'))
            .required()]

    def print_result(self, result):
        if self.args['Attribute'] == 'enableDnsHostnames':
            print self.tabify(('RETURN',
                               result['enableDnsHostnames'].get('value')))
        elif self.args['Attribute'] == 'enableDnsSupport':
            print self.tabify(('RETURN',
                               result['enableDnsSupport'].get('value')))
