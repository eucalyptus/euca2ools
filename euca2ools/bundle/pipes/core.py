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


import hashlib
import multiprocessing
import os
import shutil
import subprocess
import sys
import tarfile

import euca2ools.bundle.util


def create_bundle_pipeline(infile, outfile, enc_key, enc_iv, tarinfo):
    digest_result_mpqueue = multiprocessing.Queue()
    pids = []

    # infile -> tar
    tar_out_r, tar_out_w = euca2ools.bundle.util.open_pipe_fileobjs()
    pid = os.fork()
    pids.append(pid)
    if pid == 0:
        tar_out_r.close()
        tarball = tarfile.open(mode='w|', fileobj=tar_out_w,
                               bufsize=euca2ools.bundle.pipes._BUFSIZE)
        try:
            tarball.addfile(tarinfo, fileobj=infile)
        finally:
            infile.close()
            tarball.close()
            tar_out_w.close()
        os._exit(os.EX_OK)
    infile.close()
    tar_out_w.close()

    # tar -> sha1sum
    digest_out_r, digest_out_w = euca2ools.bundle.util.open_pipe_fileobjs()
    pid = os.fork()
    pids.append(pid)
    if pid == 0:
        digest_out_r.close()
        try:
            _calc_sha1_for_pipe(tar_out_r, digest_out_w, digest_result_mpqueue)
        finally:
            tar_out_r.close()
            digest_out_w.close()
        os._exit(os.EX_OK)
    digest_out_w.close()

    # sha1sum -> gzip
    try:
        gzip = subprocess.Popen(['pigz', '-c'], stdin=digest_out_r,
                                stdout=subprocess.PIPE, close_fds=True,
                                bufsize=-1)
    except OSError:
        gzip = subprocess.Popen(['gzip', '-c'], stdin=digest_out_r,
                                stdout=subprocess.PIPE, close_fds=True,
                                bufsize=-1)
    digest_out_r.close()
    pids.append(gzip.pid)

    # gzip -> openssl
    openssl = subprocess.Popen(['openssl', 'enc', '-e', '-aes-128-cbc',
                                '-K', enc_key, '-iv', enc_iv],
                               stdin=gzip.stdout, stdout=outfile,
                               close_fds=True, bufsize=-1)
    gzip.stdout.close()
    pids.append(openssl.pid)

    # Make sure something calls wait() on every child process
    for pid in pids:
        euca2ools.bundle.util.waitpid_in_thread(pid)

    # Return the queue the caller can use to obtain the final digest
    return digest_result_mpqueue


def create_unbundle_pipeline(infile, outfile, enc_key, enc_iv):
    digest_result_mpqueue = multiprocessing.Queue()

    # infile -> openssl
    openssl = subprocess.Popen(['openssl', 'enc', '-d', '-aes-128-cbc',
                                '-K', enc_key, '-iv', enc_iv],
                               stdin=infile, stdout=subprocess.PIPE,
                               close_fds=True, bufsize=-1)
    infile.close()
    euca2ools.bundle.util.waitpid_in_thread(openssl.pid)

    # openssl -> gzip
    try:
        gzip = subprocess.Popen(['pigz', '-c', '-d'], stdin=openssl.stdout,
                                stdout=subprocess.PIPE, close_fds=True,
                                bufsize=-1)
    except OSError:
        gzip = subprocess.Popen(['gzip', '-c', '-d'], stdin=openssl.stdout,
                                stdout=subprocess.PIPE, close_fds=True,
                                bufsize=-1)
    openssl.stdout.close()
    euca2ools.bundle.util.waitpid_in_thread(gzip.pid)

    # gzip -> sha1sum
    digest_out_r, digest_out_w = euca2ools.bundle.util.open_pipe_fileobjs()
    pid = os.fork()
    if pid == 0:
        sys.stdin.close()
        digest_out_r.close()
        try:
            _calc_sha1_for_pipe(gzip.stdout, digest_out_w,
                                digest_result_mpqueue)
        finally:
            gzip.stdout.close()
            digest_out_w.close()
        os._exit(os.EX_OK)
    gzip.stdout.close()
    digest_out_w.close()
    euca2ools.bundle.util.waitpid_in_thread(pid)

    # sha1sum -> tar
    pid = os.fork()
    if pid == 0:
        sys.stdin.close()
        tarball = tarfile.open(mode='r|', fileobj=digest_out_r)
        try:
            tarinfo = tarball.next()
            shutil.copyfileobj(tarball.extractfile(tarinfo), outfile)
        finally:
            tarball.close()
            digest_out_r.close()
            outfile.close()
        os._exit(os.EX_OK)
    digest_out_r.close()
    euca2ools.bundle.util.waitpid_in_thread(pid)

    # Return the queue the caller can use to obtain the final digest
    return digest_result_mpqueue


def copy_with_progressbar(infile, outfile, progressbar=None):
    """
    Synchronously copy data from infile to outfile, updating a progress bar
    with the total number of bytes copied along the way if one was provided.

    This method must be run on the main thread.
    """
    bytes_written = 0
    progressbar.start()
    while True:
        chunk = infile.read(euca2ools.bundle.pipes._BUFSIZE)
        if chunk:
            bytes_written += len(chunk)
            outfile.write(chunk)
        else:
            progressbar.finish()
            return
        progressbar.update(bytes_written)


def _calc_sha1_for_pipe(infile, outfile, result_mpqueue):
    """
    Read data from infile and write it to outfile, calculating a running SHA1
    digest along the way.  When infile hits end-of-file, send the digest in
    hex form to result_mpqueue and exit.
    """

    digest = hashlib.sha1()
    while True:
        chunk = infile.read(euca2ools.bundle.pipes._BUFSIZE)
        if chunk:
            digest.update(chunk)
            outfile.write(chunk)
        else:
            break
    result_mpqueue.put(digest.hexdigest())
    result_mpqueue.close()
    result_mpqueue.join_thread()
