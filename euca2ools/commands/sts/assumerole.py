# Copyright 2015 Eucalyptus Systems, Inc.
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

import datetime
import os
import pipes
import sys

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.sts import STSRequest


class AssumeRole(STSRequest):
    DESCRIPTION = '''\
        Assume an IAM role

        The %(prog)s utility obtains credentials for an IAM role and
        outputs them in the form of shellcode that sets environment
        variables that allow euca2ools commands to use them.  Use it
        inside an eval command to make this process seamless:

            $ eval `%(prog)s myrole`

        To stop using the role, use euare-releaserole(1).'''
    ARGS = [Arg('rolename', metavar='ROLE', route_to=None,
                help='the role to assume'),
            Arg('-d', '--duration', dest='DurationSeconds', metavar='SECONDS',
                type=int, default=900, help='''number of seconds the
                credentials should be valid for (900-3600) (default: 900)'''),
            Arg('--session-name', dest='RoleSessionName', metavar='PATH',
                help='''role session identifier to include in the
                assumed role user ID (default: automatic)'''),
            MutuallyExclusiveArgList(
                Arg('-c', dest='csh_output', route_to=None,
                    action='store_true', help='''generate C-shell commands on
                    stdout (default if SHELL looks like a csh-style shell'''),
                Arg('-s', dest='sh_output', route_to=None,
                    action='store_true', help='''generate Bourne shell
                    commands on stdout (default if SHELL does not look
                    like a csh-style shell''')),
            MutuallyExclusiveArgList(
                Arg('--policy-content', dest='Policy',
                    metavar='POLICY_CONTENT', help='''an IAM policy
                    further restricting what the credentials will be
                    allowed to do.  This cannot grant additional
                    permissions.'''),
                Arg('--policy-document', dest='Policy',
                    metavar='FILE', type=open, help='''file containing
                    an IAM policy further restricting what the
                    credentials will be allowed to do.  This cannot
                    grant additional permissions.''')),
            Arg('--external-id', dest='ExternalId', metavar='STR',
                help='external ID to use for comparison with policies'),
            Arg('--mfa-serial', dest='SerialNumber', metavar='MFA',
                help='MFA token serial number'),
            Arg('--mfa-code', dest='TokenCode', metavar='CODE',
                help='MFA token code')]

    def preprocess(self):
        self.params['RoleArn'] = self.__build_role_arn(
            self.args.get('rolename'))
        if not self.params.get('RoleSessionName'):
            session = datetime.datetime.utcnow().strftime(
                'euca2ools-%Y-%m-%dT%H:%M:%SZ')
            self.params['RoleSessionName'] = session

    def __build_role_arn(self, arn):
        """
        Build an ARN for a role from the fragment that was supplied at
        the command line.
        """
        if arn.count(':') == 1 and '/' not in arn:
            # Special case syntactic sugar
            arn = '{0}:role/{1}'.format(*arn.split(':'))
        if arn.count(':') == 0:
            # S3Access
            if not arn.startswith('role/'):
                arn = 'role/' + arn
            # role/A3Access
            arn = '{0}:{1}'.format(self.__get_account_id(), arn)
        if arn.count(':') == 1:
            # 123456789012:role/S3Access
            arn = ':' + arn
        if arn.count(':') == 2:
            # :123456789012:role/S3Access
            arn = 'iam:' + arn
        if arn.count(':') == 3:
            # iam::123456789012:role/S3Access
            arn = 'aws:' + arn
        if arn.count(':') == 4:
            # aws:iam::123456789012:role/S3Access
            arn = 'arn:' + arn
        # Shound be arn:aws:iam::123456789012:role/S3Access at this point
        return arn

    def __get_account_id(self):
        account_id = self.config.get_user_option('account-id')
        if not account_id:
            account_id = os.getenv('EC2_USER_ID')
        if not account_id:
            raise ArgumentError(
                'failed to determine account ID; set account-id for '
                'the user in configuration or EC2_USER_ID in the '
                'environment')
        return account_id

    def print_result(self, result):
        creds = result['Credentials']
        print '# Automatic STS credentials generated on {0}'.format(
            datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
        print '# If you can read this, rerun this program with eval:'
        print '#     eval `{0}`'.format(
            ' '.join(pipes.quote(arg) for arg in sys.argv))
        print
        # If this list changes please go update ReleaseRole.
        self.__print_var('AWS_ACCESS_KEY_ID', creds['AccessKeyId'])
        self.__print_var('AWS_ACCESS_KEY', creds['AccessKeyId'])
        self.__print_var('EC2_ACCESS_KEY', creds['AccessKeyId'])
        self.__print_var('AWS_SECRET_ACCESS_KEY', creds['SecretAccessKey'])
        self.__print_var('AWS_SECRET_KEY', creds['SecretAccessKey'])
        self.__print_var('EC2_SECRET_KEY', creds['SecretAccessKey'])
        self.__print_var('AWS_SESSION_TOKEN', creds['SessionToken'])
        self.__print_var('AWS_SECURITY_TOKEN', creds['SessionToken'])
        self.__print_var('AWS_CREDENTIAL_EXPIRATION', creds['Expiration'])
        self.__print_var('EC2_USER_ID', self.params['RoleArn'].split(':')[4])
        # Unset AWS_CREDENTIAL_FILE to avoid accidentally using its creds
        self.__print_var('AWS_CREDENTIAL_FILE', None)

    def __print_var(self, key, val):
        if (self.args.get('csh_output') or
                (not self.args.get('sh_output') and
                 os.getenv('SHELL', '').endswith('csh'))):
            if val:
                fmt = 'setenv {key} {val};'
            else:
                fmt = 'unsetenv {key};'
        else:
            if val:
                fmt = '{key}={val}; export {key};'
            else:
                fmt = 'unset {key};'
        print fmt.format(key=key, val=val)
