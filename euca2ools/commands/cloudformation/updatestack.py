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

from requestbuilder import Arg, EMPTY, MutuallyExclusiveArgList

from euca2ools.commands.argtypes import binary_tag_def, delimited_list
from euca2ools.commands.cloudformation import CloudFormationRequest
from euca2ools.commands.cloudformation.argtypes import parameter_list

class UpdateStack(CloudFormationRequest):
    """
    Update a stack's template, parameters, or capabilities
    """

    ARGS = [Arg('StackName', metavar='STACK',
                help='name of the stack to update (required)'),
            MutuallyExclusiveArgList(
                Arg('--template-file', dest='TemplateBody',
                    metavar='FILE', type=open,
                    help='file containing a new JSON template for the stack'),
                Arg('--template-url', dest='TemplateURL', metavar='URL',
                    help='URL pointing to a new JSON template for the stack')),
            Arg('--capabilities', dest='Capabilities.member',
                metavar='CAP[,...]', type=delimited_list(','),
                help='capabilities needed to update the stack'),
            Arg('-p', '--parameter', dest='param_sets', route_to=None,
                metavar='KEY=VALUE', type=parameter_list, action='append',
                help='''key and value of the parameters to use with the
                stack's template, separated by an "=" character'''),
            MutuallyExclusiveArgList(
                Arg('--tag', dest='Tags.member', metavar='KEY[=VALUE]',
                    type=binary_tag_def, action='append',
                    help='''key and optional value of a tag to add, separated
                    by an "=" character.  If no value is given the tag's value
                    is set to an empty string.'''),
                Arg('--delete-tags', dest='Tags', action='store_const',
                    const=EMPTY,
                    help='remove all tags associated with the stack'))]

    def configure(self):
        CloudFormationRequest.configure(self)
        stack_params = sum(self.args.get('param_sets') or [], [])
        self.params['Parameters.member'] = stack_params

    def preprocess(self):
        if (not self.args.get('TemplateBody') and
                not self.args.get('TemplateURL')):
            self.params['UsePreviousTemplate'] = True

    # pylint: disable=no-self-use
    def print_result(self, result):
        print result.get('StackId')
    # pylint: enable=no-self-use
