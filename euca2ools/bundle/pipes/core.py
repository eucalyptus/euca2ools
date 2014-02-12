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


def create_bundle_pipeline(infile, outfile, enc_key, enc_iv, tarinfo,
                           debug=False):
    pids = []

    # infile -> tar
    tar_out_r, tar_out_w = euca2ools.bundle.util.open_pipe_fileobjs()
    tar_p = multiprocessing.Process(target=_create_tarball_from_stream,
                                    args=(infile, tar_out_w, tarinfo),
                                    kwargs={'debug': debug})
    tar_p.start()
    pids.append(tar_p.pid)
    infile.close()
    tar_out_w.close()

    # tar -> sha1sum
    digest_out_r, digest_out_w = euca2ools.bundle.util.open_pipe_fileobjs()
    digest_result_r, digest_result_w = multiprocessing.Pipe(duplex=False)
    digest_p = multiprocessing.Process(
        target=_calc_sha1_for_pipe,
        args=(tar_out_r, digest_out_w, digest_result_w))
    digest_p.start()
    pids.append(digest_p.pid)
    digest_out_w.close()
    digest_result_w.close()

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

    # Return the connection the caller can use to obtain the final digest
    return digest_result_r


def create_unbundle_pipeline(infile, outfile, enc_key, enc_iv, debug=False):
    pids = []

    # infile -> openssl
    openssl = subprocess.Popen(['openssl', 'enc', '-d', '-aes-128-cbc',
                                '-K', enc_key, '-iv', enc_iv],
                               stdin=infile, stdout=subprocess.PIPE,
                               close_fds=True, bufsize=-1)
    infile.close()
    pids.append(openssl.pid)

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
    pids.append(gzip.pid)

    # gzip -> sha1sum
    digest_out_r, digest_out_w = euca2ools.bundle.util.open_pipe_fileobjs()
    digest_result_r, digest_result_w = multiprocessing.Pipe(duplex=False)
    pid = os.fork()
    pids.append(pid)
    if pid == 0:
        euca2ools.bundle.util.close_all_fds(
            except_fds=(gzip.stdout, digest_out_w, digest_result_w))
        try:
            _calc_sha1_for_pipe(gzip.stdout, digest_out_w,
                                digest_result_w)
        except IOError:
            if not debug:
                os._exit(os.EX_IOERR)
            raise
        finally:
            gzip.stdout.close()
            digest_out_w.close()
            digest_result_w.close()
        os._exit(os.EX_OK)
    gzip.stdout.close()
    digest_out_w.close()
    digest_result_w.close()

    # sha1sum -> tar
    pid = os.fork()
    pids.append(pid)
    if pid == 0:
        euca2ools.bundle.util.close_all_fds(except_fds=(digest_out_r, outfile))
        tarball = tarfile.open(mode='r|', fileobj=digest_out_r)
        try:
            tarinfo = tarball.next()
            shutil.copyfileobj(tarball.extractfile(tarinfo), outfile)
        except IOError:
            if not debug:
                os._exit(os.EX_IOERR)
            raise
        finally:
            tarball.close()
            digest_out_r.close()
            outfile.close()
        os._exit(os.EX_OK)
    digest_out_r.close()

    # Make sure something calls wait() on every child process
    for pid in pids:
        euca2ools.bundle.util.waitpid_in_thread(pid)

    # Return the connection the caller can use to obtain the final digest
    return digest_result_r


def copy_with_progressbar(infile, outfile, progressbar=None):
    """
    Synchronously copy data from infile to outfile, updating a progress bar
    with the total number of bytes copied along the way if one was provided,
    and return the number of bytes copied.

    This method must be run on the main thread for the progress bar to
    function correctly.
    """
    bytes_written = 0
    if progressbar is not None:
        progressbar.start()
    while True:
        chunk = infile.read(euca2ools.bundle.pipes._BUFSIZE)
        if chunk:
            bytes_written += len(chunk)
            outfile.write(chunk)
        else:
            if progressbar is not None:
                progressbar.finish()
            return bytes_written
        if progressbar is not None:
            progressbar.update(bytes_written)


def _calc_sha1_for_pipe(infile, outfile, result_mpconn):
    """
    Read data from infile and write it to outfile, calculating a running SHA1
    digest along the way.  When infile hits end-of-file, send the digest in
    hex form to result_mpconn and exit.
    """

    euca2ools.bundle.util.close_all_fds(
        except_fds=(infile, outfile, result_mpconn))
    digest = hashlib.sha1()
    while True:
        chunk = infile.read(euca2ools.bundle.pipes._BUFSIZE)
        if chunk:
            digest.update(chunk)
            outfile.write(chunk)
        else:
            break
    result_mpconn.send(digest.hexdigest())
    result_mpconn.close()
    infile.close()
    outfile.close()


def _create_tarball_from_stream(infile, outfile, tarinfo, debug=False):
    euca2ools.bundle.util.close_all_fds(except_fds=(infile, outfile))
    tarball = tarfile.open(mode='w|', fileobj=outfile,
                           bufsize=euca2ools.bundle.pipes._BUFSIZE)
    try:
        tarball.addfile(tarinfo, fileobj=infile)
    except IOError:
        # HACK
        if not debug:
            return
        raise
    finally:
        infile.close()
        tarball.close()
        outfile.close()
