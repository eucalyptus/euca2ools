# Copyright 2009-2013 Eucalyptus Systems, Inc.
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

from euca2ools.commands import Euca2ools
from euca2ools.commands.bundle.bundle import Bundle
import os.path
from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin
from requestbuilder.util import set_userregion


class Unbundle(BaseCommand, FileTransferProgressBarMixin):
    DESCRIPTION = ('Recreate an image from its bundled parts\n\nThe key used '
                   'to unbundle the image must match the certificate that was '
                   'used to bundle it.')
    SUITE = Euca2ools
    ARGS = [Arg('-m', '--manifest', metavar='FILE', required=True,
                help="the bundle's manifest file (required)"),
            Arg('-k', '--privatekey', metavar='FILE',
                help='''file containing the private key to decrypt the bundle
                with.  This must match the certificate used when bundling the
                image.'''),
            Arg('-d', '--destination', metavar='DIR', default='.',
                help='''where to place the unbundled image (default: current
                directory)'''),
            Arg('-s', '--source', metavar='DIR', default='.',
                help='''directory containing the bundled image parts (default:
                current directory)'''),
            Arg('--region', dest='userregion', metavar='USER@REGION',
                help='''use encryption keys specified for a user and/or region
                in configuration files''')]

    def configure(self):
        BaseCommand.configure(self)
        set_userregion(self.config, self.args.get('userregion'))
        set_userregion(self.config, os.getenv('EUCA_REGION'))

        if not self.args.get('privatekey'):
            config_privatekey = self.config.get_user_option('private-key')
            if self.args.get('userregion'):
                self.args['privatekey'] = config_privatekey
            elif 'EC2_PRIVATE_KEY' in os.environ:
                self.args['privatekey'] = os.getenv('EC2_PRIVATE_KEY')
            elif config_privatekey:
                self.args['privatekey'] = config_privatekey
            else:
                raise ArgumentError(
                    'missing private key; please supply one with -k')
        self.args['privatekey'] = os.path.expanduser(os.path.expandvars(
            self.args['privatekey']))
        if not os.path.exists(self.args['privatekey']):
            raise ArgumentError("private key file '{0}' does not exist"
                                .format(self.args['privatekey']))
        if not os.path.isfile(self.args['privatekey']):
            raise ArgumentError("private key file '{0}' is not a file"
                                .format(self.args['privatekey']))

    def main(self):
        bundle = Bundle.create_from_manifest(
            self.args['manifest'], partdir=self.args['source'],
            privkey_filename=self.args['privatekey'])
        pbar = self.get_progressbar(maxval=bundle.bundled_size)
        return bundle.extract_image(self.args['destination'],
                                    progressbar=pbar)

    def print_result(self, result):
        print 'Wrote', result
