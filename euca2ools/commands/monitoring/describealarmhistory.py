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

from euca2ools.commands.monitoring import CloudWatchRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse


class DescribeAlarmHistory(CloudWatchRequest, TabifyingMixin):
    DESCRIPTION = 'Retrieve history for one alarm or all alarms'
    ARGS = [Arg('AlarmName', metavar='ALARM', nargs='?',
                help='limit results to a specific alarm'),
            Arg('--end-date', dest='EndDate', metavar='DATE',
                help='limit results to history before a given point in time'),
            Arg('--history-item-type', dest='HistoryItemType',
                choices=('Action', 'ConfigurationUpdate', 'StateUpdate'),
                help='limit results to specific history item types'),
            Arg('--show-long', action='store_true', route_to=None,
                help='show detailed event data as machine-readable JSON'),
            Arg('--start-date', dest='StartDate', metavar='DATE',
                help='limit results to history after a given point in time')]
    LIST_TAGS = ['AlarmHistoryItems']

    def main(self):
        return PaginatedResponse(self, (None,), ('AlarmHistoryItems,'))

    def prepare_for_page(self, page):
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        for item in result.get('AlarmHistoryItems', []):
            bits = [item.get('AlarmName'), item.get('Timestamp'),
                    item.get('HistoryItemType'), item.get('HistorySummary')]
            if self.args['show_long']:
                bits.append(item.get('HistoryData'))
            print self.tabify(bits)
