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

from euca2ools.commands.argtypes import binary_tag_def, delimited_list
from euca2ools.commands.cloudformation import CloudFormationRequest
from euca2ools.commands.cloudformation.argtypes import parameter_list


class CreateStack(CloudFormationRequest):
    DESCRIPTION = 'Create a new stack'
    ARGS = [Arg('StackName', metavar='STACK',
                help='name of the new stack (required)'),
            MutuallyExclusiveArgList(
                Arg('--template-file', dest='TemplateBody', metavar='FILE',
                    type=open,
                    help="file containing the new stack's JSON template"),
                Arg('--template-url', dest='TemplateURL', metavar='URL',
                    help="URL pointing to the new stack's JSON template"))
            .required(),
            Arg('-d', '--disable-rollback', dest='DisableRollback',
                action='store_true', help='disable rollback on failure'),
            Arg('-n', '--notification-arns', dest='NotificationARNs',
                metavar='ARN[,...]', type=delimited_list(','), action='append',
                help='''SNS ARNs to publish stack actions to'''),
            Arg('-p', '--parameter', dest='param_sets', route_to=None,
                metavar='KEY=VALUE', type=parameter_list, action='append',
                help='''key and value of the parameters to use with the new
                stack's template, separated by an "=" character'''),
            Arg('-t', '--timeout', dest='TimeoutInMinutes', type=int,
                metavar='MINUTES', help='timeout for stack creation'),
            Arg('--tag', dest='Tags.member', metavar='KEY[=VALUE]',
                type=binary_tag_def, action='append',
                help='''key and optional value of the tag to create, separated
                by an "=" character.  If no value is given the tag's value is
                set to an empty string.''')]

    def configure(self):
        CloudFormationRequest.configure(self)
        stack_params = sum(self.args.get('param_sets') or [], [])
        self.params['Parameters.member'] = stack_params

    def print_result(self, result):
        print result.get('StackId')
