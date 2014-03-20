# Copyright 2013-2014 Eucalyptus Systems, Inc.
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

from multiprocessing import Process
import os
import subprocess
import sys
import threading
import traceback


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
    if pid_exists(pid):
        pid_thread = threading.Thread(target=check_and_waitpid, args=(pid, 0))
        pid_thread.daemon = True
        pid_thread.start()


def spawn_process(func, **kwargs):
    proc = Process(target=process_wrapper, args=[func], kwargs=kwargs)
    proc.start()
    return proc


def process_wrapper(func, **kwargs):
    name = getattr(func, '__name__', 'unknown')
    try:
        func(**kwargs)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        traceback.print_exc()
        msg = 'Error in wrapped process "{0}":{1}'.format(str(name), str(exc))
        print >> sys.stderr, msg
        return
    # pylint: disable=W0212
    # os._exit is actually public
    os._exit(os.EX_OK)
    # pylint: enable=W0212


def pid_exists(pid):
    try:
        #Check to see if pid exists
        os.kill(pid, 0)
        return True
    except OSError as ose:
        if ose.errno == os.errno.ESRCH:
            #Pid was not found
            return False
        else:
            raise ose


def check_and_waitpid(pid, status):
    if pid_exists(pid):
        try:
            os.waitpid(pid, status)
        except OSError:
            pass
