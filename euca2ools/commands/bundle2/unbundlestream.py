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
from euca2ools.bundle.pipes import fittings
from euca2ools.bundle.manifest import BundleManifest
import os
import argparse
import traceback
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.util import set_userregion
from requestbuilder.mixins import FileTransferProgressBarMixin


class UnbundleStream(BaseCommand, FileTransferProgressBarMixin):
    DESCRIPTION = ('Recreate an image from a source bundle stream\n\nThe key used '
                   'to unbundle the image must match the certificate that was '
                   'used to bundle it.')
    SUITE = Euca2ools
    ARGS = [
            Arg('-s', '--source', metavar='FILE', required=True,
                help='''Source File. Use '-' to represent <stdin>'''),
            Arg('-k', '--privatekey', metavar='FILE', required=True,
                help='''file containing the private key to decrypt the bundle
                with.  This must match the certificate used when bundling the
                image.'''),

            Arg('-m', '--manifest', dest='manifest', metavar='FILE',
                help='''Use a local manifest file to derive info about
                source stream'''),
            Arg('-e','--enc-key', dest='enc_key', #type=(lambda s: int(s, 16)),
                help='''Key used to decrypt bundled image'''),  # a hex string
            Arg('-v','--enc-iv',dest='enc_iv', #type=(lambda s: int(s, 16)),
                help='''Initialization vector used to decrypt bundled image'''),  # a hex string
            Arg('-c', '--checksum', metavar='CHECKSUM', default=None,
                help='''Bundled Image checksum, used to verify image
                resulting from this unbundle operation'''),
            Arg('-d', '--destination', metavar='DIR', default='.',
                help='''The filepath to write unbundled image to.
                If "-" is provided stdout will be used.'''),
            Arg('--maxbytes', dest='maxbytes', metavar='MAX BYTES', default=0,
                help='''The Maximum bytes allowed to be written to the
                destination.'''),
            Arg('--progressbar-label', help=argparse.SUPPRESS)]

    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)
        #self.configure()
        set_userregion(self.config, self.args.get('userregion'))
        set_userregion(self.config, os.getenv('EUCA_REGION'))

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
            raise ArgumentError("private key file '{0}' does not exist".format(self.args['privatekey']))
        if not os.path.isfile(self.args['privatekey']):
            raise ArgumentError("private key file '{0}' is not a file".format(self.args['privatekey']))
        self.private_key_path = self.args.get('privatekey')

        #Get Manifest if path provided...
        if self.args.get('manifest'):
            self.manifest_path = os.path.expanduser(os.path.abspath(self.args['manifest']))
            if not os.path.exists(self.manifest_path):
                raise ArgumentError("Manifest '{0}' does not exist".format(self.args['manifest']))
            if not os.path.isfile(self.manifest_path):
                raise ArgumentError("Manifest '{0}' is not a file".format(self.args['manifest']))
            self.manifest = BundleManifest.read_from_file(self.manifest_path, self.private_key_path)
        else:
            self.manifest = None

        #Get source file path..
        self.source_file_path = self.args['source']
        if not (self.source_file_path == "-"):
            self.source_file_path = os.path.expanduser(os.path.abspath(self.source_file_path))
            if not os.path.exists(self.source_dir):
                raise ArgumentError("Source file path '{0}' does not exist".format(self.args['source']))
            if not os.path.isfile(self.source_dir):
                raise ArgumentError("Source '{0}' is not a file".format(self.args['source']))

        #Get optional destination file path...
        self.dest_file_path = self.args['destination']
        if not (self.dest_file_path == "-"):
            self.dest_file_path = os.path.expanduser(os.path.abspath(self.args['destination']))
            if not os.path.exists(os.path.dirname(self.dest_file_path)):
                os.makedirs(self.dest_file_path, mode=0700)
            elif os.path.exists(self.dest_file_path) and not os.path.isfile(self.dest_file_path):
                raise ArgumentError("Destination '{0}' is not a file".format(self.args['destination']))


    def main(self):
        debug = self.args.get('debug')
        source_file = None
        dest_file = None
        enc_key = self.args.get('enc_key') or (self.manifest.enc_key if hasattr(self.manifest, 'enc_key') else None)
        enc_iv = self.args.get('enc_iv') or (self.manifest.enc_iv if hasattr(self.manifest, 'enc_iv') else None)
        if not enc_iv or not enc_key:
            raise ValueError('Encryption key and iv must be provided. '
                             'enc_iv:{0}, enc_key:{1})'.format(str(enc_key), str(enc_iv)))

        try:
            #Setup the destination fileobj...
            if self.dest_file_path == "-":
                #Write to stdout
                dest_file = os.fdopen(os.dup(os.sys.stdout.fileno()), 'w')
                dest_file_name = None
            else:
                #write to local file path
                dest_file = open(self.dest_file_path, 'w')
                dest_file_name = dest_file.name

            #Setup the source fileobj...
            if self.source_file_path == "-":
                source_file = os.fdopen(os.dup(os.sys.stdin.fileno()))
            else:
                source_file = open(self.source_file_path)

            #setup progress bar...
            pbar = None
            if self.manifest:
                file_size = self.manifest.image_size
            else:
                file_size = os.fstat(dest_file.fileno()).st_size
            try:
                if file_size:
                    label = self.args.get('progressbar_label', 'UnBundling image')
                    pbar = self.get_progressbar(label=label, maxval=file_size)
            except NameError: pass

            #Perform unbundle stream pipline...
            written_digest = fittings.create_unbundle_stream_pipeline(source_file,
                                                                      dest_file,
                                                                      enc_key=enc_key.strip(),
                                                                      enc_iv=enc_iv.strip(),
                                                                      progressbar=pbar,
                                                                      debug=debug,
                                                                      maxbytes=int(self.args['maxbytes']))
            written_digest = written_digest.strip()
            if dest_file:
                dest_file.close()
                #Verify the Checksum return from the unbundle operation matches what we expected in the manifest
            if self.args.get('checksum'):
                checksum = self.args.get('checksum').strip()
                if written_digest !=  checksum:
                    raise ValueError('Digest mismatch. Extracted image appears to be corrupt '
                                     '(expected digest: {0}, actual: {1})'.format(checksum, written_digest))
                self.log.debug("\nExpected digest:" + str(checksum) + "\n" +
                               "  Actual digest:" + str(written_digest))
        except KeyboardInterrupt:
            print 'Caught keyboard interrupt'
            if dest_file:
                os.remove(dest_file.name)
            return
        except Exception:
            traceback.print_exc()
            if dest_file:
                try:
                    os.remove(dest_file.name)
                except OSError:
                    print "Could not remove failed destination file."
                dest_file = None
            raise
        finally:
            if dest_file:
                dest_file.close()
            if source_file:
                source_file.close()
        return dest_file_name

    def print_result(self, result):
        if result:
            print 'Wrote', result


if __name__ == '__main__':
    UnbundleStream.run()