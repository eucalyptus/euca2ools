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

import os

from requestbuilder import Arg
from requestbuilder.auth.aws import HmacKeyAuth
from requestbuilder.command import BaseCommand
import requestbuilder.exceptions
from requestbuilder.mixins import RegionConfigurableMixin

from euca2ools.commands import Euca2ools
import euca2ools.util


class GenerateEnvironment(BaseCommand, RegionConfigurableMixin):
    DESCRIPTION = ('Read environment variables and euca2ools.ini(5) '
                   'files to discover the service URLs and credentials '
                   'for a region, then output shellcode with the '
                   'corresponding environment variables for that '
                   'information.  This output will contain secret '
                   'access keys and should be treated with care.')
    SUITE = Euca2ools
    ARGS = [Arg('--simple', action='store_true', help='''use a simpler
                output format intended for consumption by scripts'''),
            HmacKeyAuth.ARGS]

    def configure(self):
        BaseCommand.configure(self)
        self.update_config_view()

    def main(self):
        env_vars = {}
        services = euca2ools.util.generate_service_names()
        for service, service_var in services.items():
            url = os.getenv(service_var)
            if not url:
                url = self.config.get_region_option('{0}-url'.format(service))
            env_vars[service_var] = url
        auth = HmacKeyAuth(config=self.config, loglevel=self.log.level,
                           **self.args)
        try:
            auth.configure()
        except requestbuilder.exceptions.AuthError:
            self.log.info('auth configuration failed; info may be missing',
                          exc_info=True)
        env_vars['AWS_ACCESS_KEY_ID'] = auth.args.get('key_id')
        env_vars['AWS_SECRET_ACCESS_KEY'] = auth.args.get('secret_key')
        env_vars['AWS_SECURITY_TOKEN'] = auth.args.get('security_token')
        env_vars['AWS_CREDENTIAL_EXPIRATION'] = auth.args.get(
            'credential_expiration')
        env_vars['EC2_USER_ID'] = os.getenv(
            'EC2_USER_ID', self.config.get_user_option('account-id'))
        env_vars['EC2_CERT'] = os.getenv(
            'EC2_CERT', self.config.get_user_option('certificate'))
        env_vars['EC2_PRIVATE_KEY'] = os.getenv(
            'EC2_PRIVATE_KEY', self.config.get_user_option('private-key'))
        env_vars['EUCALYPTUS_CERT'] = os.getenv(
            'EUCALYPTUS_CERT', self.config.get_region_option('certificate'))
        return env_vars

    def print_result(self, env_vars):
        if self.args.get('simple'):
            for key, val in sorted(env_vars.items()):
                print '{key}={val}'.format(key=key, val=(val or ''))
        else:
            # We do this in two steps so we can put all the comments last,
            # allowing the output to work inside a shell's eval statement.
            for key, val in sorted(env_vars.items()):
                if val:
                    print '{key}={val}; export {key};'.format(key=key, val=val)
            for key, val in sorted(env_vars.items()):
                if not val:
                    print '# {key} is not set'.format(key=key)
