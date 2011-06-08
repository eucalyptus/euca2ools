# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Neil Soman neil@eucalyptus.com
#         Mitch Garnaat mgarnaat@eucalyptus.com

from boto.roboto.awsqueryrequest import AWSQueryRequest
from boto.roboto.param import Param
import euca2ools.commands.euare
import euca2ools.commands.euare.putuserpolicy


class AddUserPolicy(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = 'Add a new policy to a user'
    Params = [
        Param(name='UserName',
              short_name='u',
              long_name='user-name',
              ptype='string',
              optional=False,
              request_param=False,
              doc=""" Name of the user to associate the policy with. """),
        Param(name='PolicyName',
              short_name='p',
              long_name='policy-name',
              ptype='string',
              optional=False,
              request_param=False,
              doc=""" Name of the policy document. """),
        Param(name='Effect',
              short_name='e',
              long_name='effect',
              ptype='enum',
              choices=['Allow', 'Deny'],
              optional=False,
              request_param=False,
              doc="The value for the policy's Effect element."),
        Param(name='Action',
              short_name='a',
              long_name='action',
              ptype='string',
              optional=True,
              request_param=False,
              doc="The value for the policy's Action element"),
        Param(name='Resource',
              short_name='r',
              long_name='resource',
              ptype='string',
              optional=True,
              request_param=False,
              doc="The value for the policy's Resource element."),
        Param(name='output',
              short_name='o',
              long_name='output',
              ptype='boolean',
              optional=True,
              doc='Causes the output to include the JSON policy document created for you')]

    def build_policy(self):
        s = '{"Effect":"%s", "Action":["%s"], "Resource":["%s"]}' % (self.effect,
                                                                     self.action,
                                                                     self.resource)
        p = '{"Version":"2008-10-17","Statement":[%s]}' % s
        return p

    def cli_formatter(self, data):
        if self.cli_options.output:
            print self.policy

    def main(self, **args):
        self.process_args()
        self.user_name = self.cli_options.user_name
        self.policy_name = self.cli_options.policy_name
        self.effect = self.cli_options.effect
        if self.cli_options.action:
            self.action = self.cli_options.action
        else:
            self.action = '*'
        if self.cli_options.resource:
            self.resource = self.cli_options.resource
        else:
            self.resource = '*'
        self.policy = self.build_policy()
        obj = euca2ools.commands.euare.putuserpolicy.PutUserPolicy()
        return obj.main(user_name=self.user_name, policy_name=self.policy_name,
                        policy_document=self.policy)

    def main_cli(self):
        self.do_cli()
