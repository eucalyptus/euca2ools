# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
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

from requestbuilder import Arg
from requestbuilder.mixins import TabifyingCommand
from requestbuilder.response import PaginatedResponse
from requestbuilder.xmlparse import parse_aws_xml
from . import WalrusRequest, validate_generic_bucket_name

class ListBucket(WalrusRequest, TabifyingCommand):
    DESCRIPTION = 'List keys in one or more buckets'
    ARGS = [Arg('paths', metavar='BUCKET[/KEY]', nargs='+', route_to=None)]

    def configure(self):
        WalrusRequest.configure(self)
        for path in self.args['paths']:
            if path.startswith('/'):
                self._cli_parser.error(('argument \'{0}\' must not start with '
                        '\'/\'; format is BUCKET[/KEY]').format(path))
            bucket = path.split('/', 1)[0]
            try:
                validate_generic_bucket_name(bucket)
            except ValueError as err:
                self._cli_parser.error(
                        'bucket \'{0}\': {1}'.format(bucket, err.message))

    def main(self):
        self.method = 'GET'
        return PaginatedResponse(self, self.args['paths'], ('Contents',))

    def get_page_markers(self, response):
        if response.get('IsTruncated') == 'true':
            return {'marker': response['Contents'][-1]['Key']}

    def prepare_for_page(self, next_path, markers):
        bucket, __, prefix = next_path.partition('/')
        self.path = bucket
        if prefix:
            self.params['prefix'] = prefix
        elif 'prefix' in self.params:
            del self.params['prefix']
        if markers is not None and markers.get('marker'):
            self.params['marker'] = markers['marker']
        elif 'marker' in self.params:
            del self.params['marker']

    def parse_response(self, response):
        response_dict = self.log_and_parse_response(response,
                parse_aws_xml, list_item_markers=('Contents', 'CommonPrefixes'))
        return response_dict['ListBucketResult']

    def print_result(self, result):
        for obj in result.get('Contents', []):
            print obj.get('Key')
