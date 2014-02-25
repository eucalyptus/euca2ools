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
import tarfile
import euca2ools.bundle.util
from euca2ools.bundle.util import spawn_process, close_all_fds, pid_exists


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


def create_unbundle_pipeline(infile,
                             outfile,
                             enc_key,
                             enc_iv,
                             debug=False):
    """
    Creates a pipeline to perform the unbundle operation on infile input.
    The resulting unbundled image will be written to 'outfile'.

    :param outfile: file  obj to write unbundled image to
    :param enc_key: the encryption key used to bundle the image
    :param enc_iv: the encyrption initialization vector used in the bundle
    :returns multiprocess pipe to read sha1 digest of written image
    """
    openssl = None
    gzip = None
    sha1 = None
    tar = None
    pids = []
    try:
        # infile -> openssl
        openssl = subprocess.Popen(['openssl', 'enc', '-d', '-aes-128-cbc',
                                    '-K', enc_key, '-iv', enc_iv],
                                   stdin=infile, stdout=subprocess.PIPE,
                                   close_fds=True, bufsize=-1)
        pids.append(openssl.pid)
        infile.close()

        # openssl -> gzip
        try:
            gzip = subprocess.Popen(['pigz', '-c', '-d'], stdin=openssl.stdout,
                                    stdout=subprocess.PIPE, close_fds=True,
                                    bufsize=-1)
        except OSError:
            gzip = subprocess.Popen(['gzip', '-c', '-d'], stdin=openssl.stdout,
                                    stdout=subprocess.PIPE, close_fds=True,
                                    bufsize=-1)
        pids.append(gzip.pid)
        openssl.stdout.close()

        #Create pipe file objs to handle i/o...
        sha1_io_r, sha1_io_w = euca2ools.bundle.util.open_pipe_fileobjs()
        sha1_checksum_r, sha1_checksum_w = multiprocessing.Pipe(duplex=False)

        # gzip -> sha1sum
        sha1 = spawn_process(_calc_sha1_for_pipe,
                             infile=gzip.stdout,
                             outfile=sha1_io_w,
                             digest_out_pipe_w=sha1_checksum_w,
                             debug=debug)
        pids.append(sha1.pid)
        gzip.stdout.close()
        sha1_io_w.close()

        # sha1sum -> tar
        tar = spawn_process(_do_tar_extract,
                            infile=sha1_io_r,
                            outfile=outfile,
                            debug=debug)
        pids.append(tar.pid)
        sha1_io_r.close()
        sha1_checksum_w.close()
    except:
        try:
            sha1_checksum_r.close()
        except:
            pass
        raise

    finally:
        # Make sure something calls wait() on every child process
        for pid in pids:
            euca2ools.bundle.util.waitpid_in_thread(pid)
    return sha1_checksum_r


def copy_with_progressbar(infile, outfile, progressbar=None, maxbytes=0):
    """
    Synchronously copy data from infile to outfile, updating a progress bar
    with the total number of bytes copied along the way if one was provided,
    and return the number of bytes copied.

    This method must be run on the main thread.

    :param infile: file obj to read input from
    :param outfile: file obj to write output to
    :param progressbar: progressbar object to update with i/o information
    :param maxbytes: Int maximum number of bytes to write
    """
    bytes_written = 0
    if progressbar:
        progressbar.start()
    try:
        while not infile.closed:
            chunk = infile.read(euca2ools.bundle.pipes._BUFSIZE)
            if chunk:
                if maxbytes and ((bytes_written + len(chunk)) > maxbytes):
                    raise RuntimeError('Amount to be written:{0} will exceed '
                                       'max. Written bytes: {1}/{2}'
                                       .format(len(chunk),
                                               bytes_written,
                                               maxbytes))
                outfile.write(chunk)
                outfile.flush()
                bytes_written += len(chunk)
                if progressbar:
                    progressbar.update(bytes_written)

            else:
                break
    finally:
        if progressbar:
            progressbar.finish()
        infile.close()


def _calc_sha1_for_pipe(infile, outfile, digest_out_pipe_w, debug=False):
    """
    Read data from infile and write it to outfile, calculating a running SHA1
    digest along the way.  When infile hits end-of-file, send the digest in
    hex form to result_mpconn and exit.
    :param infile: file obj providing input for digest
    :param outfile: file obj destination for writing output
    :param digest_out_pipe_w: fileobj to write digest to
    :param debug: boolean used in exception handling
    """
    close_all_fds([infile, outfile, digest_out_pipe_w])
    digest = hashlib.sha1()
    try:
        while True:
            chunk = infile.read(euca2ools.bundle.pipes._BUFSIZE)
            if chunk:
                digest.update(chunk)
                outfile.write(chunk)
                outfile.flush()
            else:
                break
        digest_out_pipe_w.send(digest.hexdigest())
    except IOError:
        # HACK
        if not debug:
            return
        raise
    finally:
        infile.close()
        outfile.close()
        digest_out_pipe_w.close()


def _create_tarball_from_stream(infile, outfile, tarinfo, debug=False):
    close_all_fds(except_fds=[infile, outfile])
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


def _do_tar_extract(infile, outfile, debug=False):
    """
    Perform tar extract on infile and write to outfile
    :param infile: file obj providing input for tar
    :param outfile: file obj destination for tar output
    :param debug: boolean used in exception handling
    """
    close_all_fds([infile, outfile])
    tarball = tarfile.open(mode='r|', fileobj=infile)
    try:
        tarinfo = tarball.next()
        shutil.copyfileobj(tarball.extractfile(tarinfo), outfile)
    except IOError:
        # HACK
        if not debug:
            return
        raise
    finally:
        infile.close()
        tarball.close()
        outfile.close()
