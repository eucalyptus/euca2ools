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

import euca2ools.bundle.manifest
import euca2ools.bundle.pipes
import euca2ools.bundle.util


def create_bundle_part_writer(infile, part_prefix, part_size, debug=False):
    partinfo_result_r, partinfo_result_w = multiprocessing.Pipe(duplex=False)

    pid = os.fork()
    if pid == 0:
        euca2ools.bundle.util.close_all_fds(
            except_fds=(infile, partinfo_result_w))
        for part_no in itertools.count():
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
                    except IOError:
                        if not debug:
                            os._exit(os.EX_IOERR)
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
                partinfo_result_w.send(partinfo)
            if bytes_written < part_size:
                # That's the last part
                infile.close()
                partinfo_result_w.close()
                os._exit(os.EX_OK)
    partinfo_result_w.close()
    infile.close()
    euca2ools.bundle.util.waitpid_in_thread(pid)
    return partinfo_result_r


def create_mpconn_aggregator(in_mpconn, out_mpconn=None, debug=False):
    result_mpconn_r, result_mpconn_w = multiprocessing.Pipe(duplex=False)
    pid = os.fork()
    if pid == 0:
        euca2ools.bundle.util.close_all_fds(
            except_fds=(in_mpconn, out_mpconn, result_mpconn_w))
        results = []
        try:
            while True:
                next_result = in_mpconn.recv()
                results.append(next_result)
                if out_mpconn is not None:
                    out_mpconn.send(next_result)
        except EOFError:
            try:
                result_mpconn_w.send(results)
            except IOError:
                if not debug:
                    os._exit(os.EX_IOERR)
                raise
        except IOError:
            if not debug:
                os._exit(os.EX_IOERR)
            raise
        finally:
            result_mpconn_w.close()
            in_mpconn.close()
            if out_mpconn is not None:
                out_mpconn.close()
        os._exit(os.EX_OK)
    result_mpconn_w.close()
    euca2ools.bundle.util.waitpid_in_thread(pid)
    return result_mpconn_r
