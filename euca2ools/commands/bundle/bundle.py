# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import hashlib
import multiprocessing
import itertools
import logging
import os.path
import random
import subprocess
import sys
import tarfile
import threading
import time

# Note:  show_progress=True in a couple methods imports progressbar
## TODO:  document that fact


class Bundle(object):
    DEFAULT_PART_SIZE = 10 * 1024 * 1024  # 10M
    EC2_IMAGE_SIZE_LIMIT = 10 * 1024 * 1024 * 1024  # 10G

    def __init__(self):
        self.digest = None
        self.digest_algorithm = 'SHA1'
        self.enc_algorithm = 'AES-128-CBC'
        self.enc_key = None  # a hex string
        self.enc_iv = None  # a hex string
        self.image_filename = None
        self.image_size = None
        self.log = logging.getLogger(self.__class__.__name__)
        self.parts = None
        self._lock = threading.Lock()

    @property
    def bundled_size(self):
        return sum(part['size'] for part in self.parts)

    @classmethod
    def create_from_image(cls, image_filename, part_prefix, part_size=None,
                          progressbar=None):
        new_bundle = cls()
        new_bundle.__create_from_image(image_filename, part_prefix,
                                       part_size=part_size,
                                       progressbar=progressbar)
        return new_bundle

    def __create_from_image(self, image_filename, part_prefix, part_size=None,
                            progressbar=None):
        if part_size is None:
            part_size = self.DEFAULT_PART_SIZE
        with self._lock:
            self.image_filename = image_filename
            self.image_size = os.path.getsize(image_filename)
        if self.image_size > self.EC2_IMAGE_SIZE_LIMIT:
            msg = "this image is larger than EC2's size limit"
            self.log.warn(msg)
            print >> sys.stderr, 'warning:', msg
        # pipe for getting the digest from sha1sum
        digest_pipe_out, digest_pipe_in = multiprocessing.Pipe(duplex=False)
        # pipe for tar --> sha1sum
        tar_out_pipe_out, tar_out_pipe_in = os.pipe()
        # pipe for sha1sum --> gzip
        sha_out_pipe_out, sha_out_pipe_in = os.pipe()

        # tar --> sha1sum
        #
        # Digest calculation is a little processor-intensive, so it goes in its
        # own process.
        #
        # That conveniently lets us avoid the annoyances of streaming lots of
        # data between two threads by letting us simply use OS pipes.
        pid = os.fork()
        if pid == 0:
            digest_pipe_out.close()
            os.close(tar_out_pipe_in)
            os.close(sha_out_pipe_out)
            _calc_digest_and_exit(tar_out_pipe_out, sha_out_pipe_in,
                                  digest_pipe_in)
        digest_pipe_in.close()
        os.close(tar_out_pipe_out)
        os.close(sha_out_pipe_in)

        # sha1sum --> gzip
        try:
            gzip = subprocess.Popen(['pigz', '-c'], stdin=sha_out_pipe_out,
                                    stdout=subprocess.PIPE, close_fds=True,
                                    bufsize=-1)
        except OSError:
            gzip = subprocess.Popen(['gzip', '-c'], stdin=sha_out_pipe_out,
                                    stdout=subprocess.PIPE, close_fds=True,
                                    bufsize=-1)
        os.close(sha_out_pipe_out)

        # gzip --> openssl
        srand = random.SystemRandom()
        enc_key = '{0:0>32x}'.format(srand.getrandbits(128))
        enc_iv = '{0:0>32x}'.format(srand.getrandbits(128))
        with self._lock:
            self.enc_key = enc_key
            self.enc_iv = enc_iv
        openssl = subprocess.Popen(['openssl', 'enc', '-e', '-aes-128-cbc',
                                    '-K', enc_key, '-iv', enc_iv],
                                   stdin=gzip.stdout, stdout=subprocess.PIPE,
                                   close_fds=True, bufsize=-1)

        # openssl --> writer
        writer_thread = threading.Thread(target=self._write_parts,
                                         args=(openssl.stdout, part_prefix,
                                               part_size))
        writer_thread.start()

        # Drive everything by feeding tar
        with open(image_filename) as image:
            with os.fdopen(tar_out_pipe_in, 'w') as tar_input:
                _write_tarball(image, tar_input, progressbar=progressbar)
            writer_thread.join()

            overall_digest = digest_pipe_out.recv()
            digest_pipe_out.close()
            with self._lock:
                self.digest = overall_digest

    def _write_parts(self, infile, part_prefix, part_size):
        with self._lock:
            self.parts = []
        for part_no in itertools.count():
            part_fname = '{0}.part.{1}'.format(part_prefix, part_no)
            part_info = _write_single_part(infile, part_fname, part_size)
            with self._lock:
                self.parts.append(part_info)
            if part_info['size'] < part_size:
                # That's the last part
                return


### BUNDLE CREATION ###
def _write_tarball(infile, outfile, progressbar=None):
    tar_thread = threading.Thread(target=_add_fileobj_to_tarball,
                                  args=(infile, outfile))
    tar_thread.start()
    if progressbar is not None:
        progressbar.start()
        while tar_thread.is_alive():
            progressbar.update(infile.tell())
            time.sleep(0.01)
        progressbar.finish()
    tar_thread.join()


def _add_fileobj_to_tarball(infile, outfile):
    tarball = tarfile.open(mode='w|', fileobj=outfile)
    try:
        tarinfo = tarfile.TarInfo(os.path.basename(infile.name))
        tarinfo.size = os.path.getsize(infile.name)
        tarball.addfile(tarinfo=tarinfo, fileobj=infile)
    finally:
        tarball.close()


def _calc_digest_and_exit(in_fileno, out_fileno, result_pipe):
    infile = os.fdopen(in_fileno)
    outfile = os.fdopen(out_fileno, 'w')
    digest = hashlib.sha1()
    while True:
        chunk = infile.read(8192)
        if chunk:
            digest.update(chunk)
            outfile.write(chunk)
        else:
            break
    result_pipe.send(digest.hexdigest())
    result_pipe.close()
    infile.close()
    outfile.close()
    sys.exit()


def _write_single_part(infile, part_fname, part_size):
    part_digest = hashlib.sha1()
    with open(part_fname, 'w') as part:
        bytes_to_write = part_size
        while bytes_to_write > 0:
            chunk = infile.read(min((bytes_to_write, 8192)))
            if chunk:
                part.write(chunk)
                part_digest.update(chunk)
                bytes_to_write -= len(chunk)
            else:
                break
        return {'path': part_fname, 'digest': part_digest.hexdigest(),
                'size': part.tell()}
