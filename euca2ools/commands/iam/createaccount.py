# Copyright 2009-2015 Eucalyptus Systems, Inc.
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

import os.path
import sys

from requestbuilder import Arg
import requestbuilder.exceptions
from requestbuilder.mixins import TabifyingMixin
import six

from euca2ools.commands.iam import IAMRequest, arg_account_name
from euca2ools.commands.iam.createaccesskey import CreateAccessKey


CLC_CRED_CHECK_FILE = '/usr/sbin/clcadmin-assume-system-credentials'


class CreateAccount(IAMRequest, TabifyingMixin):
    DESCRIPTION = '[Eucalyptus cloud admin only] Create a new account'
    ARGS = [arg_account_name(nargs='?', help='''also add an alias (name) to the
                             new account (required on eucalyptus < 4.2)'''),
            Arg('-k', '--create-accesskey', action='store_true', route_to=None,
                help='''also create an access key for the new account's
                administrator and show it'''),
            Arg('-w', '--write-config', action='store_true', route_to=None,
                help='''output access keys and region information in the
                form of a euca2ools.ini(5) configuration file instead of
                by themselves (implies -k)'''),
            Arg('-d', '--domain', route_to=None, help='''the DNS domain to
                use for region information in configuration file output
                (default: based on IAM URL)''')]

    def configure(self):
        try:
            IAMRequest.configure(self)
        except requestbuilder.exceptions.AuthError as err:
            if (os.path.exists(CLC_CRED_CHECK_FILE) and len(err.args) > 0 and
                    isinstance(err.args[0], six.string_types)):
                msg = ("{0}.  If a cloud controller is running, you "
                       "can assume administrator credentials with "
                       "eval `clcadmin-assume-system-credentials`")
                err.args = (msg.format(err.args[0]),) + err.args[1:]
            raise

    def postprocess(self, result):
        if self.args.get('create_accesskey') or self.args.get('write_config'):
            obj = CreateAccessKey.from_other(
                self, UserName='admin',
                DelegateAccount=result['Account']['AccountId'],
                write_config=self.args.get('write_config'),
                domain=self.args.get('domain'))
            key_result = obj.main()
            result.update(key_result)

    def print_result(self, result):
        if self.args.get('write_config'):
            result['configfile'].write(sys.stdout)
        else:
            print self.tabify((result.get('Account', {}).get('AccountName'),
                               result.get('Account', {}).get('AccountId')))
            if 'AccessKey' in result:
                print result['AccessKey']['AccessKeyId']
                print result['AccessKey']['SecretAccessKey']
