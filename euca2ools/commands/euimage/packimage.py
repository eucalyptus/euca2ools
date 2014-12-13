# (C) Copyright 2014 Eucalyptus Systems, Inc.
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

from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.mixins import FileTransferProgressBarMixin

import euca2ools.commands
from euca2ools.commands.euimage.pack import ImagePack


class PackImage(BaseCommand, FileTransferProgressBarMixin):
    SUITE = euca2ools.commands.Euca2ools
    DESCRIPTION = ('***TECH PREVIEW***\n\nPack an image for simple '
                   'installation in a cloud')
    ARGS = [Arg('image_filename', metavar='IMAGE_FILE',
                help='the image to pack (required)'),
            Arg('md_filename', metavar='MD_FILE',
                help='metadata for the image to pack (required)')]

    def main(self):
        pbar = self.get_progressbar(
            label='Compressing',
            maxval=os.path.getsize(self.args['image_filename']))
        pack = ImagePack.build(self.args['md_filename'],
                               self.args['image_filename'], progressbar=pbar)
        return pack.filename

    def print_result(self, pack_filename):
        print 'Wrote', pack_filename
