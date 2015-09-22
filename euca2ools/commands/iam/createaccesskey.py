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

import inspect
import pkgutil
import sys

from requestbuilder import Arg
from requestbuilder.service import BaseService
import six

import euca2ools.commands
from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, arg_user
from euca2ools.commands.iam.getuser import GetUser
import euca2ools.exceptions


class CreateAccessKey(IAMRequest):
    DESCRIPTION = 'Create a new access key for a user'
    ARGS = [arg_user(help='''user the new key will belong to
                     (default: current user)'''),
            Arg('-w', '--write-config', action='store_true', route_to=None,
                help='''output access keys and region information in the
                form of a euca2ools.ini(5) configuration file instead of
                by themselves'''),
            Arg('-d', '--domain', route_to=None, help='''the DNS domain
                to use for region information in configuration file
                output (default: based on IAM URL)'''),
            AS_ACCOUNT]

    def postprocess(self, result):
        if self.args.get('write_config'):
            parsed = six.moves.urllib.parse.urlparse(self.service.endpoint)
            if not self.args.get('domain'):
                dnsname = parsed.netloc.split(':')[0]
                if all(label.isdigit() for label in dnsname.split('.')):
                    msg = ('warning: IAM URL {0} refers to a specific IP; '
                           'for a complete configuration file supply '
                           'the region\'s DNS domain with -d/--domain'
                           .format(self.service.endpoint))
                    print >> sys.stderr, msg
                else:
                    self.args['domain'] = parsed.netloc.split('.', 1)[1]
            configfile = six.moves.configparser.SafeConfigParser()
            if self.args.get('domain'):
                if ':' not in self.args['domain'] and ':' in parsed.netloc:
                    # Add the port
                    self.args['domain'] += ':' + parsed.netloc.split(':')[1]
                # This uses self.config.region instead of
                # self.service.region_name because the latter is a global
                # service in AWS and thus frequently deferred with "use"
                # statements.  That may eventually happen in eucalyptus
                # cloud federations as well.
                #
                # At some point an option that lets one choose a region
                # name at the command line may be useful, but until
                # someone asks for it let's not clutter it up for now.
                region_name = self.config.region or self.args['domain']
                section = 'region {0}'.format(region_name.split(':')[0])
                configfile.add_section(section)
                for service in sorted(_get_service_names()):
                    url = '{scheme}://{service}.{domain}/'.format(
                        scheme=parsed.scheme, domain=self.args['domain'],
                        service=service)
                    configfile.set(section, '{0}-url'.format(service), url)
            section = 'user {0}'.format(result['AccessKey'].get('UserName')
                                        or 'root')
            configfile.add_section(section)
            configfile.set(section, 'key-id',
                           result['AccessKey']['AccessKeyId'])
            configfile.set(section, 'secret-key',
                           result['AccessKey']['SecretAccessKey'])
            account_id = self.get_user_account_id()
            if account_id:
                configfile.set(section, 'account-id', account_id)
            result['configfile'] = configfile

    def print_result(self, result):
        if self.args.get('write_config'):
            result['configfile'].write(sys.stdout)
        else:
            print result['AccessKey']['AccessKeyId']
            print result['AccessKey']['SecretAccessKey']

    def get_user_account_id(self):
        req = GetUser.from_other(
            self, UserName=self.params['UserName'],
            DelegateAccount=self.params.get('DelegateAccount'))
        try:
            response = req.main()
        except euca2ools.exceptions.AWSError as err:
            if err.status_code == 403:
                msg = ('warning: unable to retrieve account ID ({0})'
                       .format(err.message))
                print >> sys.stderr, msg
                return None
            raise
        arn = response['User']['Arn']
        return arn.split(':')[4]


def _get_service_names():
    svcnames = ['bootstrap', 'properties', 'reporting']
    for importer, modname, ispkg in pkgutil.iter_modules(
            euca2ools.commands.__path__, euca2ools.commands.__name__ + '.'):
        module = __import__(modname, fromlist='dummy')
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and inspect.getmodule(obj) == module and
                    issubclass(obj, BaseService)):
                svcnames.append(obj.NAME)
    return svcnames
