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

import hashlib
import os
import multiprocessing

from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import (FileTransferProgressBarMixin,
                                   RegionConfigurableMixin)

from euca2ools.commands import Euca2ools
import euca2ools.bundle.pipes
from euca2ools.bundle.manifest import BundleManifest
from euca2ools.bundle.util import (close_all_fds, open_pipe_fileobjs,
                                   waitpid_in_thread)
from euca2ools.commands.bundle.unbundlestream import UnbundleStream


class Unbundle(BaseCommand, FileTransferProgressBarMixin,
               RegionConfigurableMixin):
    DESCRIPTION = ('Recreate an image from its bundled parts\n\nThe key used '
                   'to unbundle the image must match a certificate that was '
                   'used to bundle it.')
    SUITE = Euca2ools
    ARGS = [Arg('-m', '--manifest', type=open, metavar='FILE',
                required=True, help="the bundle's manifest file (required)"),
            Arg('-s', '--source', metavar='DIR', default='.',
                help='''directory containing the bundled image parts (default:
                current directory)'''),
            Arg('-d', '--destination', metavar='DIR', default='.',
                help='''where to place the unbundled image (default: current
                directory)'''),
            Arg('-k', '--privatekey', metavar='FILE', help='''file containing
                the private key to decrypt the bundle with.  This must match
                a certificate used when bundling the image.''')]

    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)
        self.update_config_view()

        # The private key could be the user's or the cloud's.  In the config
        # this is a user-level option.
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
        self.log.debug('private key: %s', self.args['privatekey'])

        if not os.path.exists(self.args.get('source', '.')):
            raise ArgumentError("argument -s/--source: directory '{0}' does "
                                "not exist".format(self.args['source']))
        if not os.path.isdir(self.args.get('source', '.')):
            raise ArgumentError("argument -s/--source: '{0}' is not a "
                                "directory".format(self.args['source']))
        if not os.path.exists(self.args.get('destination', '.')):
            raise ArgumentError("argument -d/--destination: directory '{0}' "
                                "does not exist"
                                .format(self.args['destination']))
        if not os.path.isdir(self.args.get('destination', '.')):
            raise ArgumentError("argument -d/--destination: '{0}' is not a "
                                "directory".format(self.args['destination']))

    def __read_bundle_parts(self, manifest, outfile):
        close_all_fds(except_fds=[outfile])
        for part in manifest.image_parts:
            self.log.debug("opening part '%s' for reading", part.filename)
            digest = hashlib.sha1()
            with open(part.filename) as part_file:
                while True:
                    chunk = part_file.read(euca2ools.BUFSIZE)
                    if chunk:
                        digest.update(chunk)
                        outfile.write(chunk)
                        outfile.flush()
                    else:
                        break
                actual_hexdigest = digest.hexdigest()
                if actual_hexdigest != part.hexdigest:
                    self.log.error('rejecting unbundle due to part SHA1 '
                                   'mismatch (expected: %s, actual: %s)',
                                   part.hexdigest, actual_hexdigest)
                    raise RuntimeError(
                        "bundle part '{0}' appears to be corrupt (expected "
                        "SHA1: {1}, actual: {2}"
                        .format(part.filename, part.hexdigest,
                                actual_hexdigest))

    def main(self):
        manifest = BundleManifest.read_from_fileobj(
            self.args['manifest'], privkey_filename=self.args['privatekey'])

        for part in manifest.image_parts:
            part_path = os.path.join(self.args['source'], part.filename)
            while part_path.startswith('./'):
                part_path = part_path[2:]
            if os.path.exists(part_path):
                part.filename = part_path
            else:
                raise RuntimeError(
                    "bundle part '{0}' does not exist; you may need to use "
                    "-s to specify where to find the bundle's parts"
                    .format(part_path))

        part_reader_out_r, part_reader_out_w = open_pipe_fileobjs()
        part_reader = multiprocessing.Process(
            target=self.__read_bundle_parts,
            args=(manifest, part_reader_out_w))
        part_reader.start()
        part_reader_out_w.close()
        waitpid_in_thread(part_reader.pid)

        image_filename = os.path.join(self.args['destination'],
                                      manifest.image_name)
        with open(image_filename, 'w') as image:
            unbundlestream = UnbundleStream(
                config=self.config, source=part_reader_out_r, dest=image,
                enc_key=manifest.enc_key, enc_iv=manifest.enc_iv,
                image_size=manifest.image_size,
                sha1_digest=manifest.image_digest,
                show_progress=self.args.get('show_progress', False))
            unbundlestream.main()
        return image_filename

    def print_result(self, image_filename):
        print 'Wrote', image_filename
