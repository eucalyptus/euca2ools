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

from euca2ools.commands.cloudformation import CloudFormationRequest


class ValidateTemplate(CloudFormationRequest):
    DESCRIPTION = 'Validate a CloudFormation template'
    ARGS = [MutuallyExclusiveArgList(
                Arg('--template-file', dest='TemplateBody',
                metavar='FILE', type=open,
                help='file location containing JSON template'),
                Arg('--template-url', dest='TemplateURL',
                metavar='URL', type=open,
                help='S3 url for JSON template')).required()]
    LIST_TAGS = ['Parameters', 'CapabilitiesReason', 'Capabilities']

    def print_result(self, result):
        self.tabify(('DESCRIPTION', result.get('Description')))
        for tag in self.LIST_TAGS:
            if tag in result:
                for result in result[tag]:
                    for key, value in result.items():
                        print self.tabify([tag.upper(), key, value])
