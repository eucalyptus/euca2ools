# Copyright (c) 2009-2016 Hewlett Packard Enterprise Development LP
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

import argparse
import os
import sys

from requestbuilder import Arg
import requestbuilder.auth.aws
import requestbuilder.request
import requestbuilder.service

from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from euca2ools.util import strip_response_metadata, add_fake_region_name


class IAM(requestbuilder.service.BaseService):
    NAME = 'iam'
    DESCRIPTION = 'Identity and access management service'
    API_VERSION = '2010-05-08'
    REGION_ENVVAR = 'AWS_DEFAULT_REGION'
    URL_ENVVAR = 'AWS_IAM_URL'

    ARGS = [Arg('-U', '--url', metavar='URL',
                help='identity service endpoint URL')]

    def configure(self):
        requestbuilder.service.BaseService.configure(self)
        add_fake_region_name(self)

    # pylint: disable=no-self-use
    def handle_http_error(self, response):
        raise AWSError(response)
    # pylint: enable=no-self-use


class IAMRequest(requestbuilder.request.AWSQueryRequest):
    SUITE = Euca2ools
    SERVICE_CLASS = IAM
    AUTH_CLASS = requestbuilder.auth.aws.HmacV4Auth
    METHOD = 'POST'

    def parse_response(self, response):
        response_dict = requestbuilder.request.AWSQueryRequest.parse_response(
            self, response)
        # EUARE responses enclose their useful data inside FooResponse
        # elements.  If that's all we have after stripping out ResponseMetadata
        # then just return its contents.
        return strip_response_metadata(response_dict)


AS_ACCOUNT = Arg('--as-account', dest='DelegateAccount', metavar='ACCOUNT',
                 help='''[Eucalyptus cloud admin only] run this command as
                 the administrator of another account''')


def arg_account_name(**kwargs):
    return [Arg('AccountName', metavar='ACCOUNT', **kwargs),
            Arg('-a', '--account-name', action='store_true', dest='dummy',
                route_to=None, help=argparse.SUPPRESS)]


def arg_account_alias(**kwargs):
    return [Arg('AccountAlias', metavar='ACCOUNT', **kwargs),
            Arg('-a', '--account-alias', action='store_true', dest='dummy',
                route_to=None, help=argparse.SUPPRESS)]


def arg_user(**kwargs):
    return [Arg('UserName', metavar='USER', **kwargs),
            Arg('-u', '--user-name', action='store_true', dest='dummy',
                route_to=None, help=argparse.SUPPRESS)]


def arg_group(**kwargs):
    return [Arg('GroupName', metavar='GROUP', **kwargs),
            Arg('-g', '--group-name', action='store_true', dest='dummy',
                route_to=None, help=argparse.SUPPRESS)]


def arg_role(**kwargs):
    return [Arg('RoleName', metavar='ROLE', **kwargs),
            Arg('-r', '--role-name', action='store_true', dest='dummy',
                route_to=None, help=argparse.SUPPRESS)]


def arg_iprofile(**kwargs):
    return [Arg('InstanceProfileName', metavar='IPROFILE', **kwargs),
            Arg('-s', '--instance-profile-name', action='store_true',
                dest='dummy', route_to=None, help=argparse.SUPPRESS)]


def arg_key_id(**kwargs):
    return [Arg('AccessKeyId', metavar='KEY_ID', **kwargs),
            Arg('-k', '--user-key-id', action='store_true', dest='dummy',
                route_to=None, help=argparse.SUPPRESS)]


def arg_signing_cert(**kwargs):
    return [Arg('CertificateId', metavar='CERT', **kwargs),
            Arg('-c', '--certificate-id', action='store_true',
                dest='dummy', route_to=None, help=argparse.SUPPRESS)]


def arg_server_cert(**kwargs):
    return [Arg('ServerCertificateName', metavar='CERT', **kwargs),
            Arg('-s', '--server-certificate-name', action='store_true',
                dest='dummy', route_to=None, help=argparse.SUPPRESS)]
