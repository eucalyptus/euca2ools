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

import contextlib
import hashlib
import os
import shutil
import signal
import subprocess
import tarfile
import tempfile

import euca2ools
from euca2ools.bundle.util import open_pipe_fileobjs
from euca2ools.commands.euimage.pack.metadata import (ImagePackMetadata,
                                                      ImageMetadata)


IMAGE_ARCNAME = 'image.xz'
IMAGE_MD_ARCNAME = 'image-md.yml'
PACK_MD_ARCNAME = 'pack-md.yml'


class ImagePack(object):
    def __init__(self, filename=None):
        self.pack_md = None
        self.image_md = None
        self.filename = filename
        self.__tarball = None

    @classmethod
    def open(cls, filename):
        with ImagePack(filename=filename) as pack:
            member = pack.__tarball.getmember(PACK_MD_ARCNAME)
            with contextlib.closing(pack.__tarball.extractfile(member)) \
                    as md_file:
                pack.pack_md = ImagePackMetadata.from_fileobj(md_file)
            member = pack.__tarball.getmember(IMAGE_MD_ARCNAME)
            with contextlib.closing(pack.__tarball.extractfile(member)) \
                    as md_file:
                pack.image_md = ImageMetadata.from_fileobj(md_file)
                md_file.seek(0)
                image_md_sha256sum = hashlib.sha256(md_file.read()).hexdigest()
            if image_md_sha256sum != pack.pack_md.image_md_sha256sum:
                raise RuntimeError('image metadata appears to be corrupt '
                                   '(expected SHA256: {0}, actual: {1})',
                                   pack.pack_md.image_md_sha256sum,
                                   image_md_sha256sum)
        return pack

    @classmethod
    def build(cls, image_md_filename, image_filename,
              destdir='', progressbar=None):
        pack = ImagePack()
        pack.image_md = ImageMetadata.from_file(image_md_filename)
        pack.pack_md = ImagePackMetadata()
        if destdir != '' and not os.path.isdir(destdir):
            raise ValueError('"{0}" is not a directory'.format(destdir))
        pack.filename = os.path.join(destdir, '{0}.euimage'.format(
            pack.image_md.get_nvra()))
        with open(image_md_filename) as image_md_file:
            digest = hashlib.sha256(image_md_file.read())
            pack.pack_md.image_md_sha256sum = digest.hexdigest()
        # Since we have to know the size of the compressed image ahead
        # of time to write tarinfo headers we have to spool the whole
        # thing to disk.  :-\
        with tempfile.NamedTemporaryFile() as compressed_image:
            # Feed stuff to a subprocess to checksum and compress in one pass
            digest = hashlib.sha256()
            bytes_read = 0
            with open(image_filename, 'rb') as original_image:
                xz_proc = subprocess.Popen(('xz', '-c'), stdin=subprocess.PIPE,
                                           stdout=compressed_image)
                if progressbar:
                    progressbar.start()
                while True:
                    chunk = original_image.read(euca2ools.BUFSIZE)
                    if not chunk:
                        break
                    digest.update(chunk)
                    xz_proc.stdin.write(chunk)
                    bytes_read += len(chunk)
                    if progressbar:
                        progressbar.update(bytes_read)
                xz_proc.stdin.close()
                xz_proc.wait()
            if progressbar:
                progressbar.finish()
            pack.pack_md.image_sha256sum = digest.hexdigest()
            pack.pack_md.image_size = bytes_read

            # Write metadata and pack everything up
            with contextlib.closing(tarfile.open(pack.filename, 'w',
                                                 dereference=True)) as tarball:
                with tempfile.NamedTemporaryFile() as pack_md_file:
                    pack.pack_md.dump_to_fileobj(pack_md_file)
                    tarball.add(pack_md_file.name, arcname=PACK_MD_ARCNAME)
                tarball.add(image_md_filename, arcname=IMAGE_MD_ARCNAME)
                tarball.add(compressed_image.name, arcname=IMAGE_ARCNAME)
        return pack

    def close(self):
        if self.__tarball:
            self.__tarball.close()
        self.__tarball = None

    def __enter__(self):
        assert self.filename
        self.__tarball = tarfile.open(name=self.filename, mode='r')
        return self

    def __exit__(self, type_, value, tbk):
        self.close()

    def open_image(self):
        """
        Return a file-like object that transparently yields the packed image.
        """
        assert self.filename
        with contextlib.closing(tarfile.open(name=self.filename, mode='r')) \
                as tarball:
            # This looks like it will return a file handle that will run out of
            # data as soon as we leave this with block, but since what we return
            # actually uses the read end of an os.pipe that reads from a forked
            # process things should Just Work (tm).
            return _PackedImageWrapper(tarball)


class _PackedImageWrapper(object):
    """
    A file-like object that transparently unpacks and decompresses the
    image from an image pack
    """

    def __init__(self, tarball):
        """
        This method takes a tarfile.TarFile object and spawns *two* new
        processes: an xz process for decompression and an additional
        python process that simply feeds data from the TarFile to it.
        The latter is necessary because the file-like object we get from
        TarFile.extractfile cannot be passed to a subprocess directly.

        For that reason, one is also free to close the tarball after
        this object is created.
        """
        self.__subp_pid = None
        self.__read_fh = None
        member = tarball.getmember(IMAGE_ARCNAME)
        compressed_image = tarball.extractfile(member)
        pipe_r, pipe_w = open_pipe_fileobjs()
        self.__subp_pid = os.fork()
        if self.__subp_pid == 0:
            os.setpgrp()
            pipe_r.close()
            self.__xz_proc = subprocess.Popen(
                ('xz', '-d'), stdin=subprocess.PIPE, stdout=pipe_w,
                close_fds=True)
            pipe_w.close()
            shutil.copyfileobj(compressed_image, self.__xz_proc.stdin)
            self.__xz_proc.stdin.close()
            self.__xz_proc.wait()
            os._exit(os.EX_OK)
        else:
            self.__read_fh = pipe_r

    def close(self):
        if self.__subp_pid:
            # Kill the process group
            os.kill(-os.getpgid(self.__subp_pid), signal.SIGTERM)
            self.__read_fh.close()
        else:
            os._exit(os.EX_OK)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tbk):
        self.close()

    def read(self, size=-1):
        return self.__read_fh.read(size)
