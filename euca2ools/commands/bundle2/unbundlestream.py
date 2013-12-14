# Copyright 2013 Eucalyptus Systems, Inc.
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
from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.mixins import FileTransferProgressBarMixin
from requestbuilder.util import set_userregion


class UnbundleStream(BaseCommand, FileTransferProgressBarMixin):
    DESCRIPTION = ('Recreate an image from its bundled parts using encryption '
                   'keys that are already known\n\nTo unbundle a bundle on '
                   'disk using a manifest file, use euca-unbundle.')
    SUITE = Euca2ools
    ARGS = [Arg('parts', metavar='FILE', nargs='*', default=[sys.stdin],
                help='file(s) to read the image from (default: stdin)'),
            Arg('--enc-key', metavar='HEX', required=True,
                help='hex-encoded encryption key (required)'),
            Arg('--enc-iv', metavar='HEX', required=True,
                help='hex-encoded encryption IV (required)'),
            Arg('-o', '--output', metavar='FILE', default=sys.stdout,
                help='file to write the decrypted image to (default: stdout)')]

    def configure(self):
        BaseCommand.configure(self)
        for i in range(len(self.args['parts'])):
            if isinstance(self.args['parts'], basestring):
                self.args['parts'][i] = open(self.args['parts'][i])
        if isinstance(self.args['output'], basestring):
            self.args['output'] = open(self.args['output'], 'w')

    def main(self):
        raise NotImplementedError()
