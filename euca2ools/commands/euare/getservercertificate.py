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


class GetServerCertificate(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """GetServerCertificate"""
    Params = [Param(
        name='ServerCertificateName',
        short_name='s',
        long_name='server-certificate-name',
        ptype='string',
        optional=False,
        doc=""" The name of the server certificate you want to retrieve information about. """
            ,
        )]

    Response = {u'type': u'object',
                u'name': u'GetServerCertificateResponse',
                u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the GetServerCertificate action. '
            ,
        u'type': u'object',
        u'name': u'GetServerCertificateResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' Information about the server certificate. ',
            u'type': u'object',
            u'properties': [{
                u'doc'
                    : u' The meta information of the server certificate, such as its name, path, ID, and ARN. '
                    ,
                u'type': u'object',
                u'properties': [{
                    u'min_length': 1,
                    u'type': u'string',
                    u'name': u'Path',
                    u'pattern'
                        : u'(\\u002F)|(\\u002F[\\u0021-\\u007F]+\\u002F)'
                        ,
                    u'max_length': 512,
                    u'doc'
                        : u' Path to the server certificate. For more information about paths, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                        ,
                    u'optional': False,
                    }, {
                    u'min_length': 1,
                    u'type': u'string',
                    u'name': u'ServerCertificateName',
                    u'pattern': u'[\\w+=,.@-]*',
                    u'max_length': 128,
                    u'doc'
                        : u' The name that identifies the server certificate. '
                        ,
                    u'optional': False,
                    }, {
                    u'min_length': 16,
                    u'type': u'string',
                    u'name': u'ServerCertificateId',
                    u'pattern': u'[\\w]*',
                    u'max_length': 32,
                    u'doc'
                        : u' The stable and unique string identifying the server certificate. For more information about IDs, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                        ,
                    u'optional': False,
                    }, {
                    u'min_length': 20,
                    u'name': u'Arn',
                    u'optional': False,
                    u'max_length': 2048,
                    u'doc'
                        : u' The Amazon Resource Name (ARN) specifying the server certificate. For more information about ARNs and how to use them in policies, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                        ,
                    u'type': u'string',
                    }, {
                    u'doc'
                        : u' The date when the server certificate was uploaded. '
                        ,
                    u'optional': True,
                    u'name': u'UploadDate',
                    u'type': u'dateTime',
                    }],
                u'optional': False,
                u'name': u'ServerCertificateMetadata',
                }, {
                u'min_length': 1,
                u'type': u'string',
                u'name': u'CertificateBody',
                u'pattern': u'[\\u0009\\u000A\\u000D\\u0020-\\u00FF]+',
                u'max_length': 16384,
                u'doc': u' The contents of the public key certificate. '
                    ,
                u'optional': False,
                }, {
                u'min_length': 1,
                u'type': u'string',
                u'name': u'CertificateChain',
                u'pattern': u'[\\u0009\\u000A\\u000D\\u0020-\\u00FF]*',
                u'max_length': 2097152,
                u'doc'
                    : u' The contents of the public key certificate chain. '
                    ,
                u'optional': True,
                }],
            u'optional': False,
            u'name': u'ServerCertificate',
            }],
        }, {
        u'type': u'object',
        u'optional': False,
        u'name': u'ResponseMetadata',
        u'properties': [{u'type': u'string', u'optional': False, u'name'
                        : u'RequestId'}],
        }]}


    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
