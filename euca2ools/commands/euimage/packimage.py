# (C) Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import os.path
import subprocess
import tarfile
import tempfile

from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.mixins import FileTransferProgressBarMixin

import euca2ools.commands
from euca2ools.commands.euimage import (IMAGE_ARCNAME, IMAGE_MD_ARCNAME,
                                        PACK_MD_ARCNAME)
from euca2ools.commands.euimage.metadata import (ImagePackMetadata,
                                                 ImageMetadata)


class PackImage(BaseCommand, FileTransferProgressBarMixin):
    SUITE = euca2ools.commands.Euca2ools
    DESCRIPTION = ('***TECH PREVIEW***\n\nPack an image for simple '
                   'installation in a cloud')
    ARGS = [Arg('image_filename', metavar='IMAGE_FILE',
                help='the image to pack (required)'),
            Arg('md_filename', metavar='MD_FILE',
                help='metadata for the image to pack (required)')]

    def main(self):
        # Image packs contain three files: metadata for the pack itself,
        # the image's metadata, and the compressed image.  We compress the
        # image instead of the whole archive so we can use file seeking.
        image_md = ImageMetadata.from_file(self.args['md_filename'])
        pack_md = ImagePackMetadata()
        with open(self.args['md_filename']) as image_md_file:
            digest = hashlib.sha256(image_md_file.read())
            pack_md.image_md_sha256sum = digest.hexdigest()
        pack_filename = '{0}-{1}-{2}.{3}.euimage'.format(
            image_md.name, image_md.version, image_md.release, image_md.arch)
        pack = tarfile.open(name=pack_filename, mode='w')
        # Since we have to know the size of the compressed image ahead
        # of time in order to write tarinfo headers we have to spool
        # the whole thing to disk.  :-\
        with tempfile.TemporaryFile() as compressed_image:
            # Checksum and compress the image in one pass
            digest = hashlib.sha256()
            pbar = self.get_progressbar(
                label='Compressing',
                maxval=os.path.getsize(self.args['image_filename']))
            bytes_read = 0
            with open(self.args['image_filename'], 'rb') as original_image:
                xz_proc = subprocess.Popen(('xz', '-c'), stdin=subprocess.PIPE,
                                           stdout=compressed_image)
                pbar.start()
                while True:
                    chunk = original_image.read(euca2ools.BUFSIZE)
                    if not chunk:
                        break
                    digest.update(chunk)
                    xz_proc.stdin.write(chunk)
                    bytes_read += len(chunk)
                    pbar.update(bytes_read)
                xz_proc.stdin.close()
                xz_proc.wait()
            pbar.finish()
            pack_md.image_sha256sum = digest.hexdigest()
            pack_md.image_size = bytes_read

            # Write metadata and pack everything up
            with tempfile.NamedTemporaryFile() as pack_md_file:
                pack_md.dump_to_fileobj(pack_md_file)
                pack.add(pack_md_file.name, arcname=PACK_MD_ARCNAME)
            pack.add(self.args['md_filename'], arcname=IMAGE_MD_ARCNAME)
            compressed_image.seek(0)
            tarinfo = pack.gettarinfo(fileobj=compressed_image,
                                      arcname=IMAGE_ARCNAME)
            pack.addfile(tarinfo, fileobj=compressed_image)
        return pack_filename
