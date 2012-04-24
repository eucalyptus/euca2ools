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

from argparse import SUPPRESS
from requestbuilder import Arg, Filter, GenericTagFilter
from . import EucalyptusRequest

class DescribeSnapshots(EucalyptusRequest):
    APIVersion = '2010-08-31'
    Description = 'Display information about snapshots'
    Args = [Arg('SnapshotId', nargs='*', metavar='SNAPSHOT',
                help='limit results to specific snapshots'),
            # noop for a little ec2dsnap compatibility
            Arg('--all', action='store_true', route_to=None, help=SUPPRESS),
            Arg('-o', '--owner', dest='Owner', metavar='ACCOUNT',
                action='append', default=[],
                help='limit results to snapshots owned by specific accounts'),
            Arg('-r', '--restorable-by', dest='RestorableBy', action='append',
                metavar='ACCOUNT', default=[], help='''limit results to
                snapahots restorable by specific accounts''')]
    Filters = [Filter('description', help='snapshot description'),
               Filter('owner-alias', help="snapshot owner's account alias"),
               Filter('owner-id', help="snapshot owner's account ID"),
               Filter('progress', help='snapshot progress, in percentage'),
               Filter('snapshot-id'),
               Filter('start-time', help='snapshot initiation time'),
               Filter('status', choices=('pending', 'completed', 'error')),
               Filter('tag-key', help='key of a tag assigned to the snapshot'),
               Filter('tag-value',
                      help='value of a tag assigned to the snapshot'),
               GenericTagFilter('tag:KEY',
                                help='specific tag/value combination'),
               Filter('volume-id', help='source volume ID'),
               Filter('volume-size', type=int)]
    ListMarkers = ['snapshotSet', 'tagSet']
    ItemMarkers = ['item']

    def print_result(self, result):
        for snapshot in result.get('snapshotSet', []):
            self.print_snapshot(snapshot)
