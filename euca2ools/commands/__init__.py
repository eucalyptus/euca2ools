# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2012, Eucalyptus Systems, Inc.
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

import glob
import os.path
import platform
import requestbuilder.command
import requestbuilder.request
import requests
import sys
from .. import __version__

class Euca2oolsCommand(requestbuilder.command.BaseCommand):
    def __init__(self, **kwargs):
        self._config_files = None
        requestbuilder.request.BaseCommand.__init__(self, **kwargs)

    @property
    def config_files(self):
        if self._config_files is None:
            self._config_files = ['/etc/euca2ools.ini']
            user_glob = os.path.join(os.path.expanduser('~/.euca'), '*.ini')
            self._config_files.extend(sorted(glob.glob(user_glob)))
        return self._config_files

    @staticmethod
    def print_version_and_exit():
        _print_version_and_exit()

    def __init__(self, **kwargs):
        self._config_files = None
        self.__user_agent = None
        requestbuilder.request.BaseRequest.__init__(self, **kwargs)

    @property
    def config_files(self):
        if self._config_files is None:
            self._config_files = ['/etc/euca2ools.ini']
            user_glob = os.path.join(os.path.expanduser('~/.euca'), '*.ini')
            self._config_files.extend(sorted(glob.glob(user_glob)))
        return self._config_files

    @property
    def user_agent(self):
        if self.__user_agent is None:
            user_agent_bits = ['euca2ools/{0}'.format(__version__)]

            tokens = []
            impl = platform.python_implementation()
            if impl == 'PyPy':
                impl_version = '{0}.{1}.{2}'.format(
                        sys.pypy_version_info.major,
                        sys.pypy_version_info.minor,
                        sys.pypy_version_info.micro)
                if sys.pypy_version_info.releaselevel != 'final':
                    impl_version += sys.pypy_version_info.releaselevel
            else:
                # I'm guessing for non-CPython implementations; feel free to
                # submit patches or the needed implementation-specific API
                # references.
                impl_version = platform.python_version()
            tokens.append('{0} {1}'.format(impl, impl_version))
            plat = []
            try:
                plat.append(platform.system())
                plat.append(platform.release())
            except IOError:
                pass
            if plat:
                tokens.append(' '.join(plat))
            tokens.append(platform.machine())
            user_agent_bits.append('({0})'.format('; '.join(tokens)))

            user_agent_bits.append('requestbuilder/{0}'.format(
                    requestbuilder.__version__))
            user_agent_bits.append('requests/{0}'.format(requests.__version__))
            self.__user_agent = ' '.join(user_agent_bits)
        return self.__user_agent

    @staticmethod
    def print_version_and_exit():
        _print_version_and_exit()

def _print_version_and_exit():
    print >> sys.stderr, 'euca2ools {0} (Sparta)'.format(__version__)
    if os.path.isfile('/etc/eucalyptus/eucalyptus-version'):
        with open('/etc/eucalyptus/eucalyptus-version') as version_file:
            print 'eucalyptus {0}'.format(version_file.readline().strip())
    sys.exit()
