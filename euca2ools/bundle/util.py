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


import os
import subprocess
import threading
from multiprocessing import Process
from subprocess import check_output


def close_all_fds(except_fds=None):
    except_filenos = [1, 2]
    if except_fds is not None:
        for except_fd in except_fds:
            if except_fd is None:
                pass
            elif isinstance(except_fd, int):
                except_filenos.append(except_fd)
            elif hasattr(except_fd, 'fileno'):
                except_filenos.append(except_fd.fileno())
            else:
                raise ValueError('{0} must be an int or have a fileno method'
                                 .format(repr(except_fd)))

    fileno_ranges = []
    next_range_min = 0
    for except_fileno in sorted(except_filenos):
        if except_fileno > next_range_min:
            fileno_ranges.append((next_range_min, except_fileno - 1))
        next_range_min = max(next_range_min, except_fileno + 1)
    fileno_ranges.append((next_range_min, 1024))

    for fileno_range in fileno_ranges:
        os.closerange(fileno_range[0], fileno_range[1])


def get_cert_fingerprint(cert_filename):
    openssl = subprocess.Popen(('openssl', 'x509', '-in', cert_filename,
                                '-fingerprint', '-sha1', '-noout'),
                               stdout=subprocess.PIPE)
    (fingerprint, _) = openssl.communicate()
    return fingerprint.strip().rsplit('=', 1)[-1].replace(':', '').lower()


def open_pipe_fileobjs():
    pipe_r, pipe_w = os.pipe()
    return os.fdopen(pipe_r), os.fdopen(pipe_w, 'w')

def waitpid_in_thread(pid):
    """
    Start a thread that calls os.waitpid on a particular PID to prevent
    zombie processes from hanging around after they have finished.
    """

    pid_thread = threading.Thread(target=os.waitpid, args=(pid, 0))
    pid_thread.daemon = True
    pid_thread.start()

def spawn_thread(func, **kwargs):
    t = threading.Thread(target=func, kwargs=kwargs)
    t.start()
    return t

def spawn_process(func, **kwargs):
    p = Process(target=func, kwargs=kwargs)
    p.start()
    return p

def find_and_close_open_files(exclude_files=[]):
    procs = []
    fdlist = []
    for f in exclude_files:
        fdlist.append(f.fileno())
    pid = os.getpid()
    #debug(str(pid) + ', fdlist:' + ",".join(str(x) for x in fdlist))
    proc_output = check_output(
        [ "lsof", '-w', '-Ff', "-p", str( pid ) ] )
    for fd in filter( lambda s: s and s[ 0 ] == 'f' and s[1: ].isdigit(), proc_output.split( '\n' ) ):
        procs.append(int(fd.lstrip('f')))
    #debug(str(len(procs)) + " procs for pid before:" +str(pid)+" = " + ",".join(str(x) for x in procs))
    for fd in procs:
        if fd > 3 and fdlist and not fd in fdlist:
            #debug('Closing fd:' +str(fd))
            try:
                os.close(fd)
            except Exception as e:
                pass
                #debug(str(pid) + ", Couldn't close fd:" + str(fd) + ", err:" + str(e))
    procs = []
    proc_output = check_output(
        [ "lsof", '-w', '-Ff', "-p", str( pid ) ] )
    for fd in filter( lambda s: s and s[ 0 ] == 'f' and s[1: ].isdigit(), proc_output.split( '\n' ) ):
        procs.append(int(fd.lstrip('f')))
    #debug(str(len(procs)) + " procs for pid after" +str(pid)+" = " + ",".join(str(x) for x in procs))
    return procs


