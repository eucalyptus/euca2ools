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

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.cloudformation import CloudFormationRequest


class ContinueUpdateRollback(CloudFormationRequest):
    """
    Continue rolling back a stack that has previously failed to roll back
    """

    ARGS = [Arg('StackName', metavar='STACK',
                help='name of the stack to update (required)'),
            Arg('--skip', metavar='RESOURCE', action='append',
                dest='ResourcesToSkip.member', help='''do not re-attempt
                to roll back a given resource, but instead mark it as
                UPDATE_COMPLETE without changing it.  Use this option
                multiple times to skip multiple resources.'''),
            Arg('--role', dest='RoleARN', metavar='ARN', help='''change
                the role the stack uses for this and future operations''')]

    def configure(self):
        CloudFormationRequest.configure(self)
        if (self.args.get('RoleARN') and
                not self.args['RoleARN'].startswith('arn:')):
            raise ArgumentError('argument --role: ARN must begin with "arn:"')
