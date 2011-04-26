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


class GetLoginProfile(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """GetLoginProfile"""
    Params = [Param(
        name='UserName',
        short_name='u',
        long_name='user-name',
        ptype='string',
        optional=False,
        doc=""" Name of the User whose login profile you want to retrieve. """
            ,
        )]

    Response = {u'type': u'object',
                u'name': u'GetLoginProfileResponse', u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the GetLoginProfile action. '
            ,
        u'type': u'object',
        u'name': u'GetLoginProfileResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' Login profile for the User name. ',
            u'type': u'object',
            u'properties': [{
                u'min_length': 1,
                u'type': u'string',
                u'name': u'UserName',
                u'pattern': u'[\\w+=,.@-]*',
                u'max_length': 128,
                u'doc'
                    : u' The name of the User, which can be used for logins. '
                    ,
                u'optional': False,
                }],
            u'optional': False,
            u'name': u'LoginProfile',
            }],
        }, {
        u'type': u'object',
        u'optional': False,
        u'name': u'ResponseMetadata',
        u'properties': [{u'type': u'string', u'optional': False, u'name'
                        : u'RequestId'}],
        }]}

    def cli_formatter(self, data):
        print data.LoginProfile['UserName']

    def main(self, **args):
        return self.send()

    def main_cli(self):
        self.do_cli()