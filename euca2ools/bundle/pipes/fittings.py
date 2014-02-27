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
import itertools
import multiprocessing
import os
import sys

import euca2ools.bundle.pipes
import euca2ools.bundle.util


def create_bundle_part_deleter(in_mpconn, out_mpconn=None):
    del_p = multiprocessing.Process(target=_delete_part_files,
                                    args=(in_mpconn,),
                                    kwargs={'out_mpconn': out_mpconn})
    del_p.start()
    euca2ools.bundle.util.waitpid_in_thread(del_p.pid)


def create_bundle_part_writer(infile, part_prefix, part_size,
                              part_write_sem=None, debug=False):
    partinfo_result_r, partinfo_result_w = multiprocessing.Pipe(duplex=False)

    writer_p = multiprocessing.Process(
        target=_write_parts,
        args=(infile, part_prefix, part_size, partinfo_result_w),
        kwargs={'part_write_sem': part_write_sem, 'debug': debug})
    writer_p.start()
    partinfo_result_w.close()
    infile.close()
    euca2ools.bundle.util.waitpid_in_thread(writer_p.pid)
    return partinfo_result_r


def create_mpconn_aggregator(in_mpconn, out_mpconn=None, debug=False):
    result_mpconn_r, result_mpconn_w = multiprocessing.Pipe(duplex=False)
    agg_p = multiprocessing.Process(
        target=_aggregate_mpconn_items, args=(in_mpconn, result_mpconn_w),
        kwargs={'out_mpconn': out_mpconn, 'debug': debug})
    agg_p.start()
    result_mpconn_w.close()
    euca2ools.bundle.util.waitpid_in_thread(agg_p.pid)
    return result_mpconn_r


def _delete_part_files(in_mpconn, out_mpconn=None):
    euca2ools.bundle.util.close_all_fds(except_fds=(in_mpconn, out_mpconn))
    try:
        while True:
            part = in_mpconn.recv()
            os.unlink(part.filename)
            if out_mpconn is not None:
                out_mpconn.send(part)
    except EOFError:
        return
    finally:
        in_mpconn.close()
        if out_mpconn is not None:
            out_mpconn.close()


def _aggregate_mpconn_items(in_mpconn, result_mpconn, out_mpconn=None,
                            debug=False):
    euca2ools.bundle.util.close_all_fds(
        except_fds=(in_mpconn, out_mpconn, result_mpconn))
    results = []
    try:
        while True:
            next_result = in_mpconn.recv()
            results.append(next_result)
            if out_mpconn is not None:
                out_mpconn.send(next_result)
    except EOFError:
        try:
            result_mpconn.send(results)
        except IOError:
            # HACK
            if not debug:
                return
            raise
    except IOError:
        # HACK
        if not debug:
            return
        raise
    finally:
        result_mpconn.close()
        in_mpconn.close()
        if out_mpconn is not None:
            out_mpconn.close()


def _write_parts(infile, part_prefix, part_size, partinfo_mpconn,
                 part_write_sem=None, debug=False):
    except_fds = [infile, partinfo_mpconn]
    if part_write_sem is not None and sys.platform == 'darwin':
        # When I ran close_all_fds on OS X and excluded only the FDs
        # listed above, all attempts to use the semaphore resulted in
        # complaints about bad file descriptors.  The following code
        # is a horrible hack that I stumbled upon while attempting
        # to figure out what FD number I needed to avoid closing to
        # preserve the semaphore.  It is probably incorrect and reliant
        # on implementation details, so I am happy to take a patch that
        # manages to deal with this problem in a more reasonable way.
        try:
            except_fds.append(int(part_write_sem._semlock.handle))
        except AttributeError:
            part_write_sem = None
        except ValueError:
            part_write_sem = None
    euca2ools.bundle.util.close_all_fds(except_fds=except_fds)
    for part_no in itertools.count():
        if part_write_sem is not None:
            part_write_sem.acquire()
        part_fname = '{0}.part.{1:02}'.format(part_prefix, part_no)
        part_digest = hashlib.sha1()
        with open(part_fname, 'w') as part:
            bytes_written = 0
            bytes_to_write = part_size
            while bytes_to_write > 0:
                try:
                    chunk = infile.read(
                        min(bytes_to_write,
                            euca2ools.bundle.pipes._BUFSIZE))
                except ValueError:  # I/O error on closed file
                    # HACK
                    if not debug:
                        partinfo_mpconn.close()
                        return
                    raise
                if chunk:
                    part.write(chunk)
                    part_digest.update(chunk)
                    bytes_to_write -= len(chunk)
                    bytes_written += len(chunk)
                else:
                    break
            partinfo = euca2ools.bundle.BundlePart(
                part_fname, part_digest.hexdigest(), 'SHA1', bytes_written)
            partinfo_mpconn.send(partinfo)
        if bytes_written < part_size:
            # That's the last part
            infile.close()
            partinfo_mpconn.close()
            return
