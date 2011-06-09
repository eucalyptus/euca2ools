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
import euca2ools.commands.euare.getgrouppolicy


class ListGroupPolicies(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """ListGroupPolicies"""
    Params = [
        Param(name='GroupName',
              short_name='g',
              long_name='group-name',
              ptype='string',
              optional=False,
              doc=""" The name of the group to list policies for. """),
        Param(name='policy_name',
              short_name='p',
              long_name='policy-name',
              ptype='string',
              optional=True,
              request_param=False,
              doc="""Name of the policy document to display."""),
        Param(name='verbose',
              short_name='v',
              long_name='verbose',
              ptype='boolean',
              optional=True,
              default=False,
              request_param=False,
              doc="""Displays the contents of the resulting policies (in addition to the policy names)."""),
        Param(name='Marker',
              short_name='m',
              long_name='marker',
              ptype='string',
              optional=True,
              doc=""" Use this only when paginating results, and only in a subsequent request after you've received a response where the results are truncated. Set it to the value of the Marker element in the response you just received. """),
        Param(name='MaxItems',
              short_name=None,
              long_name='max-items',
              ptype='integer',
              optional=True,
              doc=""" Use this only when paginating results to indicate the maximum number of policy names you want in the response. If there are additional policy names beyond the maximum you specify, the IsTruncated response element is true. """),
        Param(name='DelegateAccount',
              short_name=None,
              long_name='delegate',
              ptype='string',
              optional=True,
              doc=""" [Eucalyptus extension] Use the parameter only as the system admin to act as the account admin of the specified account without changing to account admin's role. """)]

    Response = {u'type': u'object',
                u'name': u'ListGroupPoliciesResponse', u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the ListGroupPolicies action. '
            ,
        u'type': u'object',
        u'name': u'ListGroupPoliciesResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' A list of policy names. ',
            u'type': u'object',
            u'properties': [{
                u'type': u'array',
                u'optional': False,
                u'name': u'member',
                u'items': [{
                    u'pattern': u'[\\w+=,.@-]*',
                    u'max_length': 128,
                    u'type': u'string',
                    u'min_length': 1,
                    }],
                }],
            u'optional': False,
            u'name': u'PolicyNames',
            }, {
            u'doc'
                : u' A flag that indicates whether there are more policy names to list. If your results were truncated, you can make a subsequent pagination request using the Marker request parameter to retrieve more policy names in the list. '
                ,
            u'optional': True,
            u'name': u'IsTruncated',
            u'type': u'boolean',
            }, {
            u'min_length': 1,
            u'type': u'string',
            u'name': u'Marker',
            u'pattern': u'[\\u0020-\\u00FF]*',
            u'max_length': 320,
            u'doc'
                : u' If IsTruncated is true, this element is present and contains the value to use for the Marker parameter in a subsequent pagination request. '
                ,
            u'optional': True,
            }],
        }, {
        u'type': u'object',
        u'optional': False,
        u'name': u'ResponseMetadata',
        u'properties': [{u'type': u'string', u'optional': False, u'name'
                        : u'RequestId'}],
        }]}

    def cli_formatter(self, data):
        group_name = self.request_params['GroupName']
        if data:
            for policy in data.PolicyNames:
                if self.cli_options.policy_name and policy != self.cli_options.policy_name:
                    continue
                if self.cli_options.verbose:
                    obj = euca2ools.commands.euare.getgrouppolicy.GetGroupPolicy()
                    data = obj.main(group_name=group_name, policy_name=policy)
                    obj.cli_formatter(data)
                else:
                    print policy

    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
