# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2013, Eucalyptus Systems, Inc.
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

from euca2ools.commands.euare import EuareRequest, AS_ACCOUNT
from requestbuilder import Arg
from requestbuilder.response import PaginatedResponse


class ListSigningCertificates(EuareRequest):
    DESCRIPTION = "List a user's signing certificates"
    ARGS = [Arg('-u', '--user-name', dest='UserName', metavar='USER',
                help='user to list certificates for (default: current user)'),
            Arg('-v', '--verbose', action='store_true', route_to=None,
                help="also show certificates' contents"),
            AS_ACCOUNT]
    LIST_TAGS = ['Certificates']

    def main(self):
        return PaginatedResponse(self, (None,), ('Certificates',))

    def prepare_for_page(self, page):
        # Pages are defined by markers
        self.params['Marker'] = page

    def get_next_page(self, response):
        if response.get('IsTruncatated') == 'true':
            return response['Marker']

    def print_result(self, result):
        for cert in result.get('Certificates', []):
            print cert['CertificateId']
            if self.args['verbose']:
                print cert['CertificateBody']
            print cert['Status']
