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

from euca2ools.commands.s3 import S3Request
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.xmlparse import parse_listdelimited_aws_xml


class ListAllMyBuckets(S3Request, TabifyingMixin):
    DESCRIPTION = 'List all buckets owned by your account'
    ARGS = [Arg('-l', dest='long_output', action='store_true', route_to=None,
                help='''list in long format, with creation dates and owner
                info'''),
            Arg('-n', dest='numeric_output', action='store_true',
                route_to=None, help='''display account IDs numerically in long
                (-l) output.  This option turns on the -l option.''')]

    def configure(self):
        S3Request.configure(self)
        if self.args['numeric_output']:
            self.args['long_output'] = True

    def preprocess(self):
        self.method = 'GET'
        self.path = ''

    def parse_response(self, response):
        response_dict = self.log_and_parse_response(
            response, parse_listdelimited_aws_xml, list_tags=('Buckets',))
        return response_dict['ListAllMyBucketsResult']

    def print_result(self, result):
        if self.args['numeric_output'] or 'DisplayName' not in result['Owner']:
            owner = result.get('Owner', {}).get('ID')
        else:
            owner = result.get('Owner', {}).get('DisplayName')

        for bucket in result.get('Buckets', []):
            if self.args['long_output']:
                print self.tabify((owner, bucket.get('CreationDate'),
                                   bucket.get('Name')))
            else:
                print bucket.get('Name')
