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

import os.path
import sys

from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.mixins import (FileTransferProgressBarMixin,
                                   RegionConfigurableMixin)

from euca2ools.bundle.pipes.core import (create_unbundle_pipeline,
                                         copy_with_progressbar)
from euca2ools.bundle.util import open_pipe_fileobjs
from euca2ools.commands import Euca2ools
from euca2ools.commands.argtypes import filesize


class UnbundleStream(BaseCommand, FileTransferProgressBarMixin,
                     RegionConfigurableMixin):
    DESCRIPTION = ('Recreate an image solely from its combined bundled parts '
                   'without using a manifest\n\nUsually one would want to use '
                   'euca-unbundle instead.')
    SUITE = Euca2ools
    ARGS = [Arg('-i', dest='source', metavar='FILE',
                help='file to read the bundle from (default: stdin)'),
            Arg('-o', dest='dest', metavar='FILE',
                help='file to write the unbundled image to (default: stdout)'),
            Arg('--enc-key', metavar='HEX', required=True, help='''the
                symmetric key used to encrypt the bundle (required)'''),
            Arg('--enc-iv', metavar='HEX', required=True,
                help='''the initialization vector used to encrypt the bundle
                (required)'''),
            Arg('--image-size', metavar='BYTES', type=filesize,
                help='verify the unbundled image is a certain size'),
            Arg('--sha1-digest', metavar='HEX', help='''verify the image's
                contents against a SHA1 digest from its manifest file''')]

    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)
        self.update_config_view()

        if not self.args.get('source') or self.args['source'] == '-':
            # We dup stdin because the multiprocessing lib closes it
            self.args['source'] = os.fdopen(os.dup(sys.stdin.fileno()))
        elif isinstance(self.args['source'], basestring):
            self.args['source'] = open(self.args['source'])
        # Otherwise, assume it is already a file object

        if not self.args.get('dest') or self.args['dest'] == '-':
            self.args['dest'] = sys.stdout
            self.args['show_progress'] = False
        elif isinstance(self.args['dest'], basestring):
            self.args['dest'] = open(self.args['dest'], 'w')
        # Otherwise, assume it is already a file object

    def main(self):
        pbar = self.get_progressbar(maxval=self.args.get('image_size'))
        unbundle_out_r, unbundle_out_w = open_pipe_fileobjs()
        unbundle_sha1_r = create_unbundle_pipeline(
            self.args['source'], unbundle_out_w, self.args['enc_key'],
            self.args['enc_iv'], debug=self.debug)
        unbundle_out_w.close()
        actual_size = copy_with_progressbar(unbundle_out_r, self.args['dest'],
                                            progressbar=pbar)
        actual_sha1 = unbundle_sha1_r.recv()
        unbundle_sha1_r.close()

        expected_sha1 = self.args.get('sha1_digest', '').lower().strip('0x')
        expected_size = self.args.get('image_size')
        if expected_sha1 and expected_sha1 != actual_sha1:
            self.log.error('rejecting unbundle due to SHA1 mismatch '
                           '(expected SHA1: %s, actual: %s)',
                           expected_sha1, actual_sha1)
            raise RuntimeError('bundle appears to be corrupt (expected SHA1: '
                               '{0}, actual: {1})'
                               .format(expected_sha1, actual_sha1))
        expected_size = self.args.get('image_size')
        if expected_size and expected_size != actual_size:
            self.log.error('rejecting unbundle due to size mismatch '
                           '(expected: %i, actual: %i)',
                           expected_size, actual_size)
            raise RuntimeError('bundle appears to be corrupt (expected size: '
                               '{0}, actual: {1})'
                               .format(expected_size, actual_size))
        return actual_sha1, actual_size
