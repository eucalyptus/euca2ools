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


class CreateSigningCertificate(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """CreateSigningCertificate"""
    Params = [Param(
        name='UserName',
        short_name='u',
        long_name='user-name',
        ptype='string',
        optional=True,
        doc=""" Name of the User the signing certificate is for. """,
        ), Param(
        name='DelegateAccount',
        short_name=None,
        long_name='delegate',
        ptype='string',
        optional=True,
        doc=""" [Eucalyptus extension] Use the parameter only as the system admin to act as the account admin of the specified account without changing to account admin's role. """,
        )]

    Response = {u'type': u'object',
                u'name': u'CreateSigningCertificateResponse',
                u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the CreateSigningCertificate action. '
            ,
        u'type': u'object',
        u'name': u'CreateSigningCertificateResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' Information about the certificate. ',
            u'type': u'object',
            u'properties': [{
                u'min_length': 1,
                u'type': u'string',
                u'name': u'UserName',
                u'pattern': u'[\\w+=,.@-]*',
                u'max_length': 128,
                u'doc'
                    : u' Name of the User the signing certificate is associated with. '
                    ,
                u'optional': False,
                }, {
                u'min_length': 24,
                u'type': u'string',
                u'name': u'CertificateId',
                u'pattern': u'[\\w]*',
                u'max_length': 128,
                u'doc': u' The ID for the signing certificate. ',
                u'optional': False,
                }, {
                u'min_length': 1,
                u'type': u'string',
                u'name': u'CertificateBody',
                u'pattern': u'[\\u0009\\u000A\\u000D\\u0020-\\u00FF]+',
                u'max_length': 16384,
                u'doc': u' The contents of the signing certificate. ',
                u'optional': False,
                }, {
                u'min_length': 1,
                u'type': u'string',
                u'name': u'PrivateKey',
                u'pattern': u'[\\u0009\\u000A\\u000D\\u0020-\\u00FF]+',
                u'max_length': 16384,
                u'doc': u' The contents of the private key. ',
                u'optional': True,
                }, {
                u'doc'
                    : u' The status of the signing certificate. Active means the key is valid for API calls, while Inactive means it is not. '
                    ,
                u'type': u'enum',
                u'name': u'Status',
                u'optional': False,
                u'choices': [u'Active', u'Inactive'],
                }, {
                u'doc'
                    : u' The date when the signing certificate was uploaded. '
                    ,
                u'optional': True,
                u'name': u'CreateDate',
                u'type': u'dateTime',
                }],
            u'optional': False,
            u'name': u'Certificate',
            }],
        }, {
        u'type': u'object',
        u'optional': False,
        u'name': u'ResponseMetadata',
        u'properties': [{u'type': u'string', u'optional': False, u'name'
                        : u'RequestId'}],
        }]}

    def cli_formatter(self, data):
        print data.Certificate['CertificateId']
        print data.Certificate['CertificateBody']
        print data.Certificate['PrivateKey']

    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
 
