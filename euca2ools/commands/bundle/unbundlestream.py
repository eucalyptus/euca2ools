# Copyright 2009-2014 Eucalyptus Systems, Inc.
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
import argparse
from euca2ools.bundle.pipes.core import create_unbundle_pipeline
from euca2ools.bundle.pipes.core import copy_with_progressbar
from euca2ools.bundle.util import open_pipe_fileobjs
from euca2ools.bundle.manifest import BundleManifest
from euca2ools.commands import Euca2ools
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import (FileTransferProgressBarMixin,
                                   RegionConfigurableMixin)


class UnbundleStream(BaseCommand, FileTransferProgressBarMixin,
                     RegionConfigurableMixin):
    DESCRIPTION = ('Recreate an image from a source bundle stream\n\n'
                   'The key used to unbundle the image must match the '
                   'certificate that was used to bundle it.')
    SUITE = Euca2ools
    ARGS = [
        Arg('-s', '--source', metavar='INFILE', default=None,
            help=argparse.SUPPRESS),
        Arg('-d', '--destination', metavar='OUTFILE', required=True,
            help='Destination path to write to. Use "-" to write to <stdout>'),
        Arg('-k', '--privatekey', metavar='FILE',
            help='''file containing the private key to decrypt the bundle
                with.  This must match the certificate used when bundling the
                image.'''),
        Arg('-m', '--manifest', dest='manifest', metavar='FILE',
            help='''Optional local manfiest path. Used to derivce encryption
            key and initialization vector for input stream'''),
        Arg('-e', '--enc-key', dest='enc_key',
            help='''Key used to decrypt bundled image'''),
        Arg('-v', '--enc-iv', dest='enc_iv',
            help='''Initialization vector used to decrypt bundled image'''),
        Arg('--maxbytes', dest='maxbytes', metavar='MAX BYTES', default=0,
            help='''The Maximum bytes allowed to be written to the
                destination.'''),
        Arg('--progressbar', dest='progressbar', help=argparse.SUPPRESS)]

    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)
        self.update_config_view()

        #Get optional destination directory...
        dest_file = self.args['destination']
        if not isinstance(dest_file, file) and dest_file != "-":
            dest_file = os.path.expanduser(os.path.abspath(dest_file))
            self.args['destination'] = dest_file

        #Get Mandatory manifest...
        manifest = self.args.get('manifest', None)
        if manifest:
            if not isinstance(manifest, BundleManifest):
                #Read manifest file into manifest obj...
                manifest_path = os.path.expanduser(os.path.abspath(
                    self.args['manifest']))
                if not os.path.exists(manifest_path):
                    raise ArgumentError("Manifest '{0}' does not exist"
                                        .format(self.args['manifest']))
                if not os.path.isfile(manifest_path):
                    raise ArgumentError("Manifest '{0}' is not a file"
                                        .format(self.args['manifest']))
                #Get the mandatory private key...
                if not self.args.get('privatekey'):
                    config_privatekey = self.config.get_user_option(
                        'private-key')
                    if self.args.get('userregion'):
                        self.args['privatekey'] = config_privatekey
                    elif 'EC2_PRIVATE_KEY' in os.environ:
                        self.args['privatekey'] = os.getenv('EC2_PRIVATE_KEY')
                    elif config_privatekey:
                        self.args['privatekey'] = config_privatekey
                    else:
                        raise ArgumentError(
                            'missing private key needed to read manifest;'
                            ' please supply one with -k')
                privatekey = self.args['privatekey']
                self.args['privatekey'] = os.path.expanduser(
                    os.path.expandvars(privatekey))
                if not os.path.exists(self.args['privatekey']):
                    raise ArgumentError("private key file '{0}' does not exist"
                                        .format(self.args['privatekey']))
                if not os.path.isfile(self.args['privatekey']):
                    raise ArgumentError("private key file '{0}' is not a file"
                                        .format(self.args['privatekey']))
                #Read manifest into BundleManifest obj...
                manifest = BundleManifest.read_from_file(
                    manifest_path,
                    self.args['privatekey'])
                self.args['manifest'] = manifest
            if not self.args.get('enc_key') and manifest:
                self.args['enc_key'] = manifest.enc_key
            if not self.args.get('enc_iv') and manifest:
                self.args['enc_iv'] = manifest.enc_iv

        if not self.args.get('enc_key') or not self.args.get('enc_iv'):
            raise ArgumentError('Encryption key (-e) and initialization vector'
                                ' (-v) are required if manifest (-m) is not'
                                ' provided')

    def main(self):
        pbar = self.args.get('progressbar', None)
        manifest = self.args.get('manifest')
        enc_key = self.args.get('enc_key')
        enc_iv = self.args.get('enc_iv')
        debug = self.args.get('debug')
        maxbytes = self.args.get('maxbytes')

        #Setup the destination fileobj...
        if isinstance(self.args.get('destination'), file):
            #Use provided file obj...
            self.log.debug('Writing image to provided fileobj')
            dest_file = self.args.get('destination')
            dest_file_name = str(dest_file.name)
            self.log.debug('Writing image to provided fileobj:'
                           + dest_file_name)
        elif self.args.get('destination') == '-':
            #Use stdout...
            self.log.debug('Writing image to stdout')
            dest_file_name = '<stdout>'
            dest_file = os.fdopen(os.dup(os.sys.stdout.fileno()), 'w')
        else:
            #Open file at path provided...
            self.log.debug('Writing image to ')
            dest_file_name = self.args.get('destination')
            dest_file = open(self.args.get('destination'), 'w')

        #Start the unbundle...
        try:
            if self.args.get('source') and not self.args.get('source') == "-":
                if isinstance(self.args.get('source'), file):
                    self.log.debug('Reading from provided fileobj')
                    infile = self.args.get('source')
                else:
                    self.log.debug('Reading from file at path %s',
                                   str(self.args.get('source')))
                    infile = open(self.args.get('source'))
            else:
                #Unbundle from stdin stream...
                self.log.debug('Reading from stdin')
                infile = os.fdopen(os.dup(os.sys.stdin.fileno()))
            try:
                progress_r, progress_w = open_pipe_fileobjs()
                sha1pipe = create_unbundle_pipeline(
                    infile=infile, outfile=progress_w, enc_key=enc_key,
                    enc_iv=enc_iv, debug=debug)
                progress_w.close()
                copy_with_progressbar(infile=progress_r, outfile=dest_file,
                                      progressbar=pbar, maxbytes=maxbytes)
                progress_r.close()
            finally:
                if infile:
                    infile.close()
                if progress_r:
                    progress_r.close()
                if progress_w:
                    progress_w.close()
            digest = sha1pipe.recv()
            if manifest:
                #Verify the resulting unbundled Checksum matches the manifest
                if digest != manifest.image_digest:
                    raise ValueError('Digest mismatch. '
                                     'Extracted image appears to be corrupt '
                                     '(expected digest: {0}, actual: {1})'
                                     .format(manifest.image_digest, digest))
                self.log.debug("\nExpected digest:{0}\n  Actual digest:{1}"
                               .format(manifest.image_digest, digest))
            self.log.debug('Wrote stream to destination:' + dest_file_name)
            self.log.debug('Digest for unbundled image:' + str(digest))
        except KeyboardInterrupt:
            print 'Caught keyboard interrupt'
            return
        return digest

    def print_result(self, result):
        if result and self.args.get('debug'):
            print 'Finished unbundle stream. ', result


if __name__ == '__main__':
    UnbundleStream.run()
