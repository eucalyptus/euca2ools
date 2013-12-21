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
import os.path
from StringIO import StringIO
from euca2ools.bundle.pipes.core import create_unbundle_by_manifest_pipeline, create_unbundle_by_inputfile_pipeline
from euca2ools.bundle.manifest import BundleManifest
from os import remove, pipe, fdopen
import os
import pty
import time
import traceback
import hashlib
from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.util import set_userregion
#from requestbuilder.mixins import FileTransferProgressBarMixin

try:
    from progressbar import ProgressBar, Bar, Percentage,ETA
except:pass



class Unbundle(BaseCommand):
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

    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)
        set_userregion(self.config, self.args.get('userregion'))
        set_userregion(self.config, os.getenv('EUCA_REGION'))

        #Get Mandatory manifest...
        if not self.args.get('manifest'):
            raise ArgumentError('missing manifest; please supply one with -m')
        self.manifest_path = os.path.expanduser(os.path.abspath(self.args['manifest']))
        if not os.path.exists(self.manifest_path):
            raise ArgumentError("Manifest '{0}' does not exist".format(self.args['manifest']))
        if not os.path.isfile(self.manifest_path):
            raise ArgumentError("Manifest '{0}' is not a file".format(self.args['manifest']))

        #Get the mandatory private key...
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
        self.private_key_path = self.args.get('privatekey')

        #Get optional source directory...
        self.source_dir = os.path.expanduser(os.path.abspath(self.args['source']))
        if not os.path.exists(self.source_dir):
            raise ArgumentError("Source directory '{0}' does not exist".format(self.args['source']))
        if not os.path.isdir(self.source_dir):
            raise ArgumentError("Source '{0}' is not Directory".format(self.args['source']))

        #Get optional destination directory...
        self.dest_dir = os.path.expanduser(os.path.abspath(self.args['destination']))
        if not os.path.exists(self.source_dir):
            raise ArgumentError("Source directory '{0}' does not exist".format(self.args['destination']))
        if not os.path.isdir(self.source_dir):
            raise ArgumentError("Source '{0}' is not Directory".format(self.args['destination']))


    def main(self):
        manifest = BundleManifest.read_from_file(self.manifest_path, self.private_key_path)
        dest_file = open(self.dest_dir + "/" + manifest.image_name, 'w')
        try:
            widgets=[Percentage(), Bar(), ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=manifest.image_size)
        except Exception as pe:
            pbar = None
        try:
            mpq = create_unbundle_by_manifest_pipeline(dest_file, manifest, self.source_dir, pbar)
            written_digest = mpq.get()
            print "Expected digest:" + str(manifest.image_digest)
            print "  Actual digest:" + str(written_digest)
            if dest_file:
                dest_file.close()
            if written_digest != manifest.image_digest:
                raise ValueError('extracted image appears to be corrupt '
                                 '(expected digest: {0}, actual: {1})'.format(manifest.image_digest, written_digest))
        except Exception:
            traceback.print_exc()
            if dest_file:
                os.remove(dest_file.name)
            raise
        finally:
            dest_file.close()
        return dest_file.name


    def print_result(self, result):
        print 'Wrote', result


if __name__ == '__main__':
    Unbundle.run()