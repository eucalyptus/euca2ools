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
import euca2ools.bundle.pipes
from euca2ools.bundle.util import open_pipe_fileobjs, spawn_process
from euca2ools.bundle.util import close_all_fds, waitpid_in_thread
from euca2ools.bundle.manifest import BundleManifest
from euca2ools.commands.bundle2.unbundlestream import UnbundleStream
import os
import hashlib
import argparse
import traceback
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.util import set_userregion
from requestbuilder.mixins import FileTransferProgressBarMixin


class Unbundle(BaseCommand, FileTransferProgressBarMixin):
    DESCRIPTION = ('Recreate an image from its bundled parts\n\nThe key used '
                   'to unbundle the image must match the certificate that was '
                   'used to bundle it.')
    SUITE = Euca2ools
    ARGS = [Arg('-m', '--manifest', dest='manifest', metavar='FILE',
                required=True,
                help='''use a local manifest file to figure out what to
                download'''),
            Arg('-s', '--source', metavar='DIR', default='.',
                help='''directory containing the bundled image parts (default:
                current directory). If "-" is provided stdin will be used.'''),
            Arg('-k', '--privatekey', metavar='FILE', required=True,
                help='''file containing the private key to decrypt the bundle
                with.  This must match the certificate used when bundling the
                image.'''),
            Arg('-d', '--destination', metavar='DIR', default='.',
                help='''where to place the unbundled image (default: current
                directory). If "-" is provided stdout will be used.'''),
            Arg('--maxbytes', dest='maxbytes', metavar='MAX BYTES', default=0,
                help='''The Maximum bytes allowed to be written to the
                destination.'''),
            Arg('--progressbar-label', help=argparse.SUPPRESS)]

    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)
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
            raise ArgumentError("private key file '{0}' does not exist"
                                .format(self.args['privatekey']))
        if not os.path.isfile(self.args['privatekey']):
            raise ArgumentError("private key file '{0}' is not a file"
                                .format(self.args['privatekey']))

        #Get optional source directory...
        source = self.args['source']
        if source != "-":
            source = os.path.expanduser(os.path.abspath(source))
            if not os.path.exists(source):
                raise ArgumentError("Source directory '{0}' does not exist"
                                    .format(self.args['source']))
            if not os.path.isdir(source):
                raise ArgumentError("Source '{0}' is not Directory"
                                    .format(self.args['source']))
        self.args['source'] = source

        #Get optional destination directory...
        dest_dir = self.args['destination']
        if not (dest_dir == "-"):
            dest_dir = os.path.expanduser(os.path.abspath(dest_dir))
            if not os.path.exists(dest_dir):
                raise ArgumentError("Destination directory '{0}' does"
                                    " not exist".format(dest_dir))
            if not os.path.isdir(dest_dir):
                raise ArgumentError("Destination '{0}' is not Directory"
                                    .format(dest_dir))
        self.args['destination'] = dest_dir

        #Get Mandatory manifest...
        if not isinstance(self.args.get('manifest'), BundleManifest):
            manifest_path = os.path.expanduser(os.path.abspath(
                self.args['manifest']))
            if not os.path.exists(manifest_path):
                raise ArgumentError("Manifest '{0}' does not exist"
                                    .format(self.args['manifest']))
            if not os.path.isfile(manifest_path):
                raise ArgumentError("Manifest '{0}' is not a file"
                                    .format(self.args['manifest']))
                #Read manifest into BundleManifest obj...
            self.args['manifest'] = (BundleManifest.
                                     read_from_file(manifest_path,
                                                    self.args['privatekey']))

        self.args['maxbytes'] = int(self.args.get('maxbytes', 0))

    def _concatenate_parts_to_file_for_pipe(self,
                                            outfile,
                                            image_parts,
                                            source_dir,
                                            debug=False):
        """
        Concatenate a list of 'image_parts' (files) found in 'source_dir' into
        pipeline fed by 'outfile'. Parts are checked against checksum contained
        in part obj against calculated checksums as they are read/written.

        :param outfile: file obj used to output concatenated parts to
        :param image_parts: list of euca2ools.manifest.part objs
        :param source_dir: local path to parts contained in image_parts
        :param debug: boolean used in exception handling
        """
        close_all_fds([outfile])
        part_count = len(image_parts)
        part_file = None
        try:
            for part in image_parts:
                self.log.debug("Concatenating Part:" + str(part.filename))
                sha1sum = hashlib.sha1()
                part_file_path = source_dir + "/" + part.filename
                with open(part_file_path) as part_file:
                    data = part_file.read(euca2ools.bundle.pipes._BUFSIZE)
                    while data:
                        sha1sum.update(data)
                        outfile.write(data)
                        outfile.flush()
                        data = part_file.read(euca2ools.bundle.pipes._BUFSIZE)
                    part_digest = sha1sum.hexdigest()
                    self.log.debug(
                        "PART NUMBER:" + str(image_parts.index(part) + 1) +
                        "/" + str(part_count))
                    self.log.debug('Part sha1sum:' + str(part_digest))
                    self.log.debug('Expected sum:' + str(part.hexdigest))
                    if part_digest != part.hexdigest:
                        raise ValueError('Input part file may be corrupt:{0} '
                                         .format(part.filename),
                                         '(expected digest: {0}, actual: {1})'
                                         .format(part.hexdigest, part_digest))
        except IOError as ioe:
            # HACK
            self.log.debug('Error in _concatenate_parts_to_file_for_pipe.' +
                           str(ioe))
            if not debug:
                return
            raise ioe
        finally:
            if part_file:
                part_file.close()
            self.log.debug('Concatentate done')
            self.log.debug('Closing write end of pipe after writing')
            outfile.close()

    def main(self):
        dest_dir = self.args.get('destination')
        manifest = self.args.get('manifest')

        #Setup the destination fileobj...
        if dest_dir == "-":
            #Write to stdout
            dest_file = os.fdopen(os.dup(os.sys.stdout.fileno()), 'w')
            dest_file_name = None
        else:
            #write to local file path...
            dest_file = open(dest_dir + "/" + manifest.image_name, 'w')
            dest_file_name = dest_file.name
            #check for avail space if the resulting image size is known
            if manifest:
                d_stat = os.statvfs(dest_file_name)
                avail_space = d_stat.f_frsize * d_stat.f_favail
                if manifest.image_size > avail_space:
                    raise ValueError('Image size:{0} exceeds destination free '
                                     'space:{1}'
                                     .format(manifest.image_size, avail_space))

        #setup progress bar...
        try:
            label = self.args.get('progressbar_label', 'UnBundling image')
            pbar = self.get_progressbar(label=label,
                                        maxval=manifest.image_size)
        except NameError:
            pbar = None

        try:
            #Start the unbundle...
            unbundle_r, unbundle_w = open_pipe_fileobjs()
            writer = spawn_process(self._concatenate_parts_to_file_for_pipe,
                                   outfile=unbundle_w,
                                   image_parts=manifest.image_parts,
                                   source_dir=self.args.get('source'),
                                   debug=self.args.get('debug'))
            unbundle_w.close()
            waitpid_in_thread(writer.pid)
            self.log.debug('Using enc key:' + str(manifest.enc_key))
            self.log.debug('using enc iv:' + str(manifest.enc_iv))
            digest = UnbundleStream(source=unbundle_r,
                                    destination=dest_file,
                                    enc_key=manifest.enc_key,
                                    enc_iv=manifest.enc_iv,
                                    progressbar=pbar,
                                    maxbytes=self.args.get('maxbytes'),
                                    config=self.config).main()
            digest = digest.strip()
            if dest_file:
                dest_file.close()
            #Verify the Checksum matches the manifest
            if digest != manifest.image_digest:
                raise ValueError('Digest mismatch. Extracted image appears '
                                 'to be corrupt (expected digest: {0}, '
                                 'actual: {1})'
                                 .format(manifest.image_digest, digest))
            self.log.debug("\nExpected digest:{0}\n  Actual digest:{1}"
                           .format(str(manifest.image_digest), str(digest)))
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
            print 'Wrote ', result


if __name__ == '__main__':
    Unbundle.run()
