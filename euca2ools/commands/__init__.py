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
from .. import __version__, __codename__

class Euca2oolsCommand(requestbuilder.command.BaseCommand):
    Version = 'euca2ools {0} ({1})'.format(__version__, __codename__)

    def __init__(self, **kwargs):
        self.ConfigFiles.append('/etc/euca2ools.ini')
        user_config_glob = os.path.join(os.path.expanduser('~/.euca'), '*.ini')
        for configfile in sorted(glob.glob(user_config_glob)):
            self.ConfigFiles.append(configfile)
        requestbuilder.request.BaseCommand.__init__(self, **kwargs)

class Euca2oolsRequest(Euca2oolsCommand, requestbuilder.request.BaseRequest):
    def __init__(self, **kwargs):
        Euca2oolsCommand.__init__(self, **kwargs)
        requestbuilder.request.BaseRequest.__init__(self, **kwargs)
        self.__user_agent = None

    @property
    def user_agent(self):
        if not self.__user_agent:
            template = ('euca2ools/{ver} ({os} {osver}; {python} {pyver}) '
                        'requestbuilder/{rqver}')
            self.__user_agent = template.format(ver=__version__,
                    os=platform.uname()[0], osver=platform.uname()[2],
                    python=platform.python_implementation(),
                    pyver=platform.python_version(),
                    rqver=requestbuilder.__version__)
        return self.__user_agent
