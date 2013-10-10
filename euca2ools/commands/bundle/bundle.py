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

import binascii
import hashlib
import multiprocessing
import itertools
import logging
import lxml.objectify
import os.path
import random
import shutil
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
        self.digest_algorithm = None
        self.enc_algorithm = None
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
        new_bundle._create_from_image(image_filename, part_prefix,
                                      part_size=part_size,
                                      progressbar=progressbar)
        return new_bundle

    @classmethod
    def create_from_manifest(cls, manifest_filename, partdir=None,
                             privkey_filename=None):
        if partdir is None:
            partdir = os.path.dirname(manifest_filename)
        new_bundle = cls()
        with open(manifest_filename) as manifest_file:
            # noinspection PyUnresolvedReferences
            manifest = lxml.objectify.parse(manifest_file).getroot()
        new_bundle.digest = manifest.image.digest.text
        new_bundle.digest_algorithm = manifest.image.digest.get('algorithm')
        new_bundle.enc_algorithm = manifest.image.user_encrypted_key.get(
            'algorithm')
        new_bundle.enc_key = _try_to_decrypt_keys(
            (manifest.image.user_encrypted_key.text,
             manifest.image.ec2_encrypted_key.text), privkey_filename)
        new_bundle.enc_iv = _try_to_decrypt_keys(
            (manifest.image.user_encrypted_iv.text,
             manifest.image.ec2_encrypted_iv.text), privkey_filename)
        new_bundle.image_size = int(manifest.image.size.text)
        new_bundle.parts = []
        for part in manifest.image.parts.part:
            part_dict = {}
            part_filename = os.path.join(partdir, part.filename.text)
            if not os.path.isfile(part_filename):
                raise ValueError("no such part: '{0}'".format(part_filename))
            part_dict['path'] = part_filename
            part_dict['digest'] = part.digest.text
            part_dict['size'] = os.path.getsize(part_filename)
            new_bundle.parts.append(part_dict)
        return new_bundle

    def _create_from_image(self, image_filename, part_prefix, part_size=None,
                           progressbar=None):
        if part_size is None:
            part_size = self.DEFAULT_PART_SIZE
        with self._lock:
            self.digest_algorithm = 'SHA1'
            self.enc_algorithm = 'AES-128-CBC'
            self.image_filename = image_filename
            self.image_size = os.path.getsize(image_filename)
        if self.image_size > self.EC2_IMAGE_SIZE_LIMIT:
            msg = "this image is larger than EC2's size limit"
            self.log.warn(msg)
            print >> sys.stderr, 'warning:', msg
        elif self.image_size == 0:
            msg = 'this image is an empty file'
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
        try:
            for part_no in itertools.count():
                part_fname = '{0}.part.{1}'.format(part_prefix, part_no)
                part_info = _write_single_part(infile, part_fname, part_size)
                with self._lock:
                    self.parts.append(part_info)
                if part_info['size'] < part_size:
                    # That's the last part
                    return
        finally:
            infile.close()

    def extract_image(self, destdir, progressbar=None):
        assert self.digest_algorithm == 'SHA1'
        assert self.enc_algorithm == 'AES-128-CBC'

        # pipe for getting the digest from sha1sum
        digest_pipe_out, digest_pipe_in = multiprocessing.Pipe(duplex=False)
        # pipe for getting the extracted image's file name from tar
        imgname_pipe_out, imgname_pipe_in = multiprocessing.Pipe(duplex=False)
        # pipe for gzip -> sha1sum
        gzip_out_pipe_out, gzip_out_pipe_in = os.pipe()
        # pipe for sha1sum -> tar
        sha_out_pipe_out, sha_out_pipe_in = os.pipe()

        # part reader -> openssl
        openssl = subprocess.Popen(['openssl', 'enc', '-d', '-aes-128-cbc',
                                    '-K', self.enc_key, '-iv', self.enc_iv],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, bufsize=-1)

        # openssl -> gzip
        try:
            subprocess.Popen(['pigz', '-c', '-d'], stdin=openssl.stdout,
                             stdout=gzip_out_pipe_in, close_fds=True,
                             bufsize=-1)
        except OSError:
            subprocess.Popen(['gzip', '-c', '-d'], stdin=openssl.stdout,
                             stdout=gzip_out_pipe_in, close_fds=True,
                             bufsize=-1)
        openssl.stdout.close()
        os.close(gzip_out_pipe_in)

        # gzip -> sha1sum
        pid = os.fork()
        if pid == 0:
            openssl.stdin.close()
            digest_pipe_out.close()
            os.close(sha_out_pipe_out)
            _calc_digest_and_exit(gzip_out_pipe_out, sha_out_pipe_in,
                                  digest_pipe_in)
        digest_pipe_in.close()
        os.close(gzip_out_pipe_out)
        os.close(sha_out_pipe_in)

        tar_thread = threading.Thread(
            target=_extract_image_from_tarball,
            args=(os.fdopen(sha_out_pipe_out), destdir, imgname_pipe_in))
        tar_thread.start()

        # Drive everything by feeding each part in turn to openssl
        bytes_read = 0  # progressbar must be based on bundled_size, not size
        progressbar.start()
        try:
            for part in self.parts:
                with open(part['path']) as part_file:
                    while True:
                        chunk = part_file.read(8192)
                        if chunk:
                            openssl.stdin.write(chunk)
                            bytes_read += len(chunk)
                            progressbar.update(bytes_read)
                        else:
                            break
        finally:
            openssl.stdin.close()
        progressbar.finish()
        tar_thread.join()

        written_digest = digest_pipe_out.recv()
        digest_pipe_out.close()
        with self._lock:
            self.image_filename = imgname_pipe_out.recv()
            imgname_pipe_out.close()
            if written_digest != self.digest:
                raise ValueError('extracted image appears to be corrupt '
                                 '(expected digest: {0}, actual: {1})'
                                 .format(self.digest, written_digest))
            if os.path.getsize(self.image_filename) != self.image_size:
                raise ValueError('extracted image appears to be corrupt '
                                 '(expected size: {0}, actual: {1})'
                                 .format(self.image_size,
                                         os.path.getsize(self.image_filename)))
        return self.image_filename


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


### BUNDLE EXTRACTION ###
def _get_bundle_keys_from_manifest(manifest, privkey_filename):
    enc_key = _try_to_decrypt_keys((manifest.image.user_encrypted_key.text,
                                    manifest.image.ec2_encrypted_key.text),
                                   privkey_filename)
    enc_iv = _try_to_decrypt_keys((manifest.image.user_encrypted_iv.text,
                                   manifest.image.ec2_encrypted_iv.text),
                                  privkey_filename)
    return enc_key, enc_iv


def _try_to_decrypt_keys(hex_encrypted_keys, privkey_filename):
    for key in hex_encrypted_keys:
        popen = subprocess.Popen(['openssl', 'rsautl', '-decrypt', '-pkcs',
                                  '-inkey', privkey_filename],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (decrypted_key, __) = popen.communicate(binascii.unhexlify(key))
        try:
            # Make sure it might actually be an encryption key.
            # This isn't perfect, but it's still better than nothing.
            int(decrypted_key, 16)
            return decrypted_key
        except ValueError:
            pass
    raise ValueError("Failed to decrypt the bundle's encryption key.  "
                     "Ensure the key supplied matches the one used for "
                     "bundling.")


def _extract_image_from_tarball(infile, destdir, imgname_pipe):
    tarball = tarfile.open(mode='r|', fileobj=infile)
    try:
        tarinfo = tarball.next()
        assert tarinfo is not None
        outfile_name = os.path.join(destdir, tarinfo.name)
        imgname_pipe.send(outfile_name)
        imgname_pipe.close()
        tarred_image = tarball.extractfile(tarinfo)
        with open(outfile_name, 'w') as outfile:
            shutil.copyfileobj(tarred_image, outfile)
    finally:
        tarball.close()
