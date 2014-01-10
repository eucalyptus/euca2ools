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
from euca2ools.commands.walrus import WalrusRequest

from euca2ools.commands.bundle.helpers import get_manifest_keys
import euca2ools.bundle.pipes
from euca2ools.bundle.pipes import fittings
from euca2ools.bundle.manifest import BundleManifest
import os
import lxml.objectify
import argparse
import traceback
from StringIO import StringIO
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.util import set_userregion
from requestbuilder.mixins import FileTransferProgressBarMixin



class Unbundle(WalrusRequest, FileTransferProgressBarMixin):
    DESCRIPTION = ('Recreate an image from its bundled parts\n\nThe key used '
                   'to unbundle the image must match the certificate that was '
                   'used to bundle it.')
    SUITE = Euca2ools
    ARGS = [MutuallyExclusiveArgList(
                Arg('-m', '--manifest', dest='manifest', metavar='FILE',
                    help='''use a local manifest file to figure out what to
                    download'''),
                Arg('-p', '--prefix', metavar='PREFIX',
                    help='''download the bundle that begins with a specific
                    prefix (e.g. "fry" for "fry.manifest.xml")''')),
            MutuallyExclusiveArgList(
                Arg('-b', '--bucket', metavar='BUCKET',
                    help='bucket to download the bucket from (required)'),
                Arg('-s', '--source', metavar='DIR', default='.',
                    help='''directory containing the bundled image parts (default:
                    current directory). If "-" is provided stdin will be used.''')),
            Arg('-k', '--privatekey', metavar='FILE', required=True,
                help='''file containing the private key to decrypt the bundle
                with.  This must match the certificate used when bundling the
                image.'''),
            Arg('-c', '--checksum', metavar='CHECKSUM', default=None,
                help='''Bundled Image checksum, used to verify image
                resulting from this unbundle operation'''),
            Arg('-d', '--destination', metavar='DIR', default='.',
                help='''where to place the unbundled image (default: current
                directory). If "-" is provided stdout will be used.'''),
            #Arg('--region', dest='userregion', metavar='USER@REGION',
            #    help='''use encryption keys specified for a user and/or region
            #    in configuration files'''),
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


        #Get Mandatory manifest...
        if self.args.get('manifest'):
            self.manifest_path = os.path.expanduser(os.path.abspath(self.args['manifest']))
            if not os.path.exists(self.manifest_path):
                raise ArgumentError("Manifest '{0}' does not exist".format(self.args['manifest']))
            if not os.path.isfile(self.manifest_path):
                raise ArgumentError("Manifest '{0}' is not a file".format(self.args['manifest']))
        else:
            self.manifest_path = None


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

        #Get optional source directory...
        self.source_dir = self.args['source']
        if not (self.source_dir == "-"):
            self.source_dir = os.path.expanduser(os.path.abspath(self.source_dir))
            if not os.path.exists(self.source_dir):
                raise ArgumentError("Source directory '{0}' does not exist".format(self.args['source']))
            if not os.path.isdir(self.source_dir):
                raise ArgumentError("Source '{0}' is not Directory".format(self.args['source']))

        #Get optional destination directory...
        self.dest_dir = self.args['destination']
        if not (self.dest_dir == "-"):
            self.dest_dir = os.path.expanduser(os.path.abspath(self.args['destination']))
            if not os.path.exists(self.dest_dir):
                raise ArgumentError("Destination directory '{0}' does not exist".format(self.args['destination']))
            if not os.path.isdir(self.dest_dir):
                raise ArgumentError("Destination '{0}' is not Directory".format(self.args['destination']))

    def _get_manifest(self):
        if self.manifest_path:
            return(BundleManifest.read_from_file(self.manifest_path, self.private_key_path))
        else:
            bucket = self.args.get('bucket')
            prefix = self.args.get('prefix')
            manifest_keys = get_manifest_keys(bucket, prefix, service=self.service,
                                              config=self.config)
            if len(manifest_keys) > 1:
                raise RuntimeError('Found multiple manifests:{0}'.format(",".join(str(m) for m in manifest_keys)))
            self.path = os.path.join(bucket, manifest_keys.pop())

            #todo write/read manifest into pipe when converting to xml obj instead
            manifest_f = StringIO()
            self._download_to_file_obj( path=self.path, outfile=manifest_f)
            manifest_f.seek(0)
            xml = lxml.objectify.parse(manifest_f).getroot()
            manifest = BundleManifest._parse_manifest_xml(xml, self.private_key_path)
            manifest_f.close()
            self.log.debug('Got Manifest for image:' + str(manifest.image_name))
            return manifest

    def _download_to_file_obj(self, path, outfile):
        #chunk_size = 16384
        chunk_size = euca2ools.bundle.pipes._BUFSIZE
        try:
            self.path = path
            response = self.send()
            bytes_written = 0
            for chunk in response.iter_content(chunk_size=chunk_size):
                outfile.write(chunk)
                outfile.flush()
                bytes_written += len(chunk)
        finally:
            self.log.debug('Downloaded bytes:{0} file:{1}'.format( bytes_written,path))


    def main(self):
        manifest = self._get_manifest()
        debug = self.args.get('debug')

        #Setup the destination fileobj...
        if self.dest_dir == "-":
            #Write to stdout
            dest_file = os.fdopen(os.dup(os.sys.stdout.fileno()), 'w')
            dest_file_name = None
        else:
            #write to local file path
            dest_file = open(self.dest_dir + "/" + manifest.image_name, 'w')
            dest_file_name = dest_file.name

        #setup progress bar...
        try:
            label = self.args.get('progressbar_label', 'UnBundling image')
            pbar = self.get_progressbar(label=label,
                                        maxval=manifest.image_size)
        except NameError:
            pbar = None

        try:
            if self.source_dir == '-':
                #Unbundle stdin stream...
                written_digest = fittings.create_unbundle_stream_pipeline(os.fdopen(os.dup(os.sys.stdin.fileno())),
                                                                dest_file,
                                                                enc_key=manifest.enc_key,
                                                                enc_iv=manifest.enc_iv,
                                                                progressbar=pbar,
                                                                debug= debug,
                                                                maxbytes=int(self.args['maxbytes']))
            elif self.manifest_path:
                #Unbundle parts in a local directory
                written_digest = fittings.create_unbundle_by_local_manifest_pipeline(dest_file,
                                                                      manifest,
                                                                      self.source_dir,
                                                                      pbar,
                                                                      debug=debug,
                                                                      maxbytes=int(self.args['maxbytes']))
            else:
                #Unbundle a remote bundle
                written_digest = fittings.create_unbundle_by_remote_manifest_pipeline(dest_file,
                                                                                      self.args.get('bucket'),
                                                                                      manifest,
                                                                                      self,
                                                                                      pbar,
                                                                                      debug=debug,
                                                                                      maxbytes=0
                                                                                      )

            written_digest = written_digest.strip()
            if dest_file:
                dest_file.close()
            #Verify the Checksum return from the unbundle operation matches what we expected in the manifest
            if written_digest != manifest.image_digest:
                raise ValueError('Digest mismatch. Extracted image appears to be corrupt '
                                 '(expected digest: {0}, actual: {1})'.format(manifest.image_digest, written_digest))
            self.log.debug("\nExpected digest:" + str(manifest.image_digest) + "\n" +
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
            raise
        finally:
            dest_file.close()
        return dest_file_name


    def print_result(self, result):
        if result:
            print 'Wrote', result


if __name__ == '__main__':
    Unbundle.run()