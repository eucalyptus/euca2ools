# Copyright (c) 2016 Hewlett Packard Enterprise Development LP
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


class GetTemplateSummary(CloudFormationRequest):
    DESCRIPTION = "Summarize a template"
    ARGS = [MutuallyExclusiveArgList(
        Arg('StackName', metavar='STACK', nargs='?', help='''name or ID of the
            stack (names cannot be used for deleted stacks)'''),
        Arg('--template-file', dest='TemplateBody',
            metavar='FILE', type=open,
            help='file location containing JSON template'),
        Arg('--template-url', dest='TemplateURL',
            metavar='URL', help='S3 URL for JSON template'))
            .required()]
    LIST_TAGS = ['AllowedValues', 'Capabilities', 'Parameters',
                 'ResourceTypes']

    def print_result(self, result):
        if result.get('Description'):
            print self.tabify(('DESCRIPTION', result.get('Description')))
        for cap in result.get('Capabilities') or []:
            print self.tabify(('CAPABILITY', cap))
        if result.get('CapabilitiesReason'):
            print self.tabify(('CAPABILITYREASON',
                               result.get('CapabilitiesReason')))
        for res in result.get('ResourceTypes') or []:
            print self.tabify(('RESOURCETYPES', res))
        for param in result.get('Parameters') or []:
            print self.tabify(('PARAMETER', param.get('ParameterKey'),
                               param.get('NoEcho'), param.get('DefaultValue'),
                               param.get('Description')))
            for allowed in ((param.get('ParameterConstraints') or {})
                            .get('AllowedValues') or []):
                print self.tabify(('ALLOWED-VALUE', param.get('ParameterKey'),
                                   allowed))
        if result.get('Metadata'):
            print self.tabify(('METADATA', result.get('Metadata')))
