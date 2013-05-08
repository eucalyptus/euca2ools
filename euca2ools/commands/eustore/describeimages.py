# Software License Agreement (BSD License)
#
# Copyright (c) 2011-2013, Eucalyptus Systems, Inc.
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

from euca2ools.commands.eustore import EuStoreRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin


class DescribeImages(EuStoreRequest, TabifyingMixin):
    DESCRIPTION = 'List images available for installation from EuStore'
    ARGS = [Arg('-v', '--verbose', action='store_true',
                help='display more information about images than the default')]

    def preprocess(self):
        self.path = 'catalog'
        # Requests 1 adds Transfer-Encoding: chunked unconditionally when
        # self.body is None.  emis.eucalyptus.com currently runs nginx without
        # the module needed for that loaded, so this hacks around it.
        self.body = ''

    def parse_response(self, response):
        self.log.debug('-- response content --\n', extra={'append': True})
        self.log.debug(response.text, extra={'append': True})
        self.log.debug('-- end of response content --')
        return response.json()

    def print_result(self, catalog):
        for image in catalog.get('images', []):
            hypervisors = image.get('hypervisors-supported', [])
            bits = [image.get('name'), image.get('os'),
                    image.get('architecture'), image.get('version'),
                    ','.join(hypervisors), image.get('description')]
            if self.args['verbose']:
                bits.extend([image.get('date'), image.get('stamp'),
                             image.get('recipe'), image.get('contact')])
            print self.tabify(bits)
