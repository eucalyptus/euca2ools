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
import traceback
import time
from StringIO import StringIO
from multiprocessing import Process
from subprocess import check_output

show_debug = False


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


def waitpid_in_thread(pid, pname='unknown name', debug=False):
    """
    Start a thread that calls os.waitpid on a particular PID to prevent
    zombie processes from hanging around after they have finished.
    """
    if pid_exists(pid):
        if debug:
            monitor_thread = threading.Thread(target=monitor_pid, args=(pid, pname))
            monitor_thread.daemon = True
            monitor_thread.start()
        pid_thread = threading.Thread(target=check_and_waitpid, args=(pid, 0))
        pid_thread.daemon = True
        pid_thread.start()

def spawn_process(func, **kwargs):
    p = Process(target=process_wrapper, args=[func], kwargs=kwargs)
    p.start()
    return p


def process_wrapper(func, **kwargs):
    if hasattr(func, '__name__'):
        name = func.__name__
    else:
        name = 'unknown func'
    print_debug('Attempting to run:' + str(name) + ', with kwargs:' + str(kwargs))
    try:
        func(**kwargs)
    except KeyboardInterrupt:
        pass
    except Exception, e:
        try:
            out = StringIO()
            traceback.print_exception(*os.sys.exc_info(), file=out)
            out.seek(0)
            tb = out.read()
        except Exception, e:
            tb = "Could not get traceback" + str(e)
        msg = 'Error in wrapped process:' + str(name) + ":" + str(e) + "\n" + str(tb)
        print >> os.sys.stderr, msg
        return
        os._exit(1)
    os._exit(os.EX_OK)

def monitor_pid(pid, name):
    for x in xrange(0,10):
        print >> os.sys.stderr, \
            'Does process ' + str(name) + ':(' + str(pid) + ') exist? '\
            + str(pid_exists(pid))
        time.sleep(5)

def pid_exists(pid):
    try:
        #Check to see if pid exists
        os.kill(pid, 0)
        return True
    except OSError, ose:
        if ose.errno == os.errno.ESRCH:
            return False
        else:
            raise ose


def check_and_waitpid(pid, status):
    if pid_exists(pid):
        try:
            os.waitpid(pid, status)
        except OSError:
            pass


def print_debug(msg, *args):
    if show_debug:
        msg += " ".join(str(x) for x in args)
        print >> os.sys.stderr, msg