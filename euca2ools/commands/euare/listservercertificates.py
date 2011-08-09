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


class ListServerCertificates(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """ListServerCertificates"""
    Params = [Param(
        name='PathPrefix',
        short_name='p',
        long_name='path-prefix',
        ptype='string',
        optional=True,
        doc=""" The path prefix for filtering the results. For example: /company/servercerts would get all server certificates for which the path starts with /company/servercerts.  This parameter is optional. If it is not included, it defaults to a slash (/), listing all server certificates. """
            ,
        ), Param(
        name='Marker',
        short_name='m',
        long_name='marker',
        ptype='string',
        optional=True,
        doc=""" Use this only when paginating results, and only in a subsequent request after you've received a response where the results are truncated. Set it to the value of the Marker element in the response you just received. """
            ,
        ), Param(
        name='MaxItems',
        short_name=None,
        long_name='max-items',
        ptype='integer',
        optional=True,
        doc=""" Use this only when paginating results to indicate the maximum number of server certificates you want in the response. If there are additional server certificates beyond the maximum you specify, the IsTruncated response element will be set to true. """
            ,
        )]

    Response = {u'type': u'object',
                u'name': u'ListServerCertificatesResponse',
                u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the ListServerCertificates action. '
            ,
        u'type': u'object',
        u'name': u'ListServerCertificatesResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' A list of server certificates. ',
            u'type': u'object',
            u'properties': [{
                u'type': u'array',
                u'optional': False,
                u'name': u'member',
                u'items': [{u'doc'
                           : u' ServerCertificateMetadata contains information about a server certificate without its certificate body, certificate chain, and private key.  This data type is used as a response element in the action UploadServerCertificate and ListServerCertificates. '
                           , u'type': u'object', u'properties': [{
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
                    }]}],
                }],
            u'optional': False,
            u'name': u'ServerCertificateMetadataList',
            }, {
            u'doc'
                : u' A flag that indicates whether there are more server certificates to list. If your results were truncated, you can make a subsequent pagination request using the Marker request parameter to retrieve more server certificates in the list. '
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

    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
