# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
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

import os.path
from requestbuilder.exceptions import ArgumentError


def add_bundle_creds(args, config):
    # User's X.509 certificate (user-level in config)
    if not args.get('cert'):
        config_cert = config.get_user_option('x509-cert')
        if 'EC2_CERT' in os.environ:
            args['cert'] = os.getenv('EC2_CERT')
        elif config_cert:
            args['cert'] = config_cert
    if args.get('cert'):
        args['cert'] = os.path.expanduser(os.path.expandvars(args['cert']))
        if not os.path.exists(args['cert']):
            raise ArgumentError("certificate file '{0}' does not exist"
                                .format(args['cert']))
        if not os.path.isfile(args['cert']):
            raise ArgumentError("certificate file '{0}' is not a file"
                                .format(args['cert']))

    # User's private key (user-level in config)
    if not args.get('privatekey'):
        config_privatekey = config.get_user_option('x509-key')
        if 'EC2_PRIVATE_KEY' in os.environ:
            args['privatekey'] = os.getenv('EC2_PRIVATE_KEY')
        elif config_privatekey:
            args['privatekey'] = config_privatekey
    if args.get('privatekey'):
        args['privatekey'] = os.path.expanduser(os.path.expandvars(
            args['privatekey']))
        if not os.path.exists(args['privatekey']):
            raise ArgumentError("private key file '{0}' does not exist"
                                .format(args['privatekey']))
        if not os.path.isfile(args['privatekey']):
            raise ArgumentError("private key file '{0}' is not a file"
                                .format(args['privatekey']))

    # Cloud's X.509 cert (region-level in config)
    if not args.get('ec2cert'):
        config_privatekey = config.get_region_option('x509-cert')
        if 'EUCALYPTUS_CERT' in os.environ:
            # This has no EC2 equivalent since they just bundle their cert.
            args['ec2cert'] = os.getenv('EUCALYPTUS_CERT')
        elif config_privatekey:
            args['ec2cert'] = config_privatekey
    if args.get('ec2cert'):
        args['ec2cert'] = os.path.expanduser(os.path.expandvars(
            args['ec2cert']))
        if not os.path.exists(args['ec2cert']):
            raise ArgumentError("cloud certificate file '{0}' does not exist"
                                .format(args['ec2cert']))
        if not os.path.isfile(args['ec2cert']):
            raise ArgumentError("cloud certificate file '{0}' is not a file"
                                .format(args['ec2cert']))

    # User's account ID (user-level)
    if not args.get('user'):
        config_account_id = config.get_user_option('account-id')
        if 'EC2_USER_ID' in os.environ:
            args['user'] = os.getenv('EC2_USER_ID')
        elif config_account_id:
            args['user'] = config_account_id
