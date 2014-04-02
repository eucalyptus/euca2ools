# Copyright 2009-2013 Eucalyptus Systems, Inc.
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

from euca2ools.commands.euca import EucalyptusRequest
from requestbuilder import Arg, Filter, GenericTagFilter
from requestbuilder.exceptions import ArgumentError


class DescribeSnapshots(EucalyptusRequest):
    DESCRIPTION = ('Show information about snapshots\n\nBy default, only '
                   'snapshots your account owns and snapshots for which your '
                   'account has explicit restore permissions are shown.')
    ARGS = [Arg('SnapshotId', nargs='*', metavar='SNAPSHOT',
                help='limit results to specific snapshots'),
            Arg('-a', '--all', action='store_true', route_to=None,
                help='describe all snapshots'),
            Arg('-o', '--owner', dest='Owner', metavar='ACCOUNT',
                action='append', default=[],
                help='limit results to snapshots owned by specific accounts'),
            Arg('-r', '--restorable-by', dest='RestorableBy', action='append',
                metavar='ACCOUNT', default=[], help='''limit results to
                snapahots restorable by specific accounts''')]
    FILTERS = [Filter('description', help='snapshot description'),
               Filter('owner-alias', help="snapshot owner's account alias"),
               Filter('owner-id', help="snapshot owner's account ID"),
               Filter('progress', help='snapshot progress, in percentage'),
               Filter('snapshot-id'),
               Filter('start-time', help='snapshot initiation time'),
               Filter('status'),
               Filter('tag-key', help='key of a tag assigned to the snapshot'),
               Filter('tag-value',
                      help='value of a tag assigned to the snapshot'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('volume-id', help='source volume ID'),
               Filter('volume-size', type=int)]
    LIST_TAGS = ['snapshotSet', 'tagSet']

    # noinspection PyExceptionInherit
    def configure(self):
        EucalyptusRequest.configure(self)
        if self.args.get('all'):
            if self.args.get('Owner'):
                raise ArgumentError('argument -a/--all: not allowed with '
                                    'argument -o/--owner')
            if self.args.get('RestorableBy'):
                raise ArgumentError('argument -a/--all: not allowed with '
                                    'argument -r/--restorable-by')

    def main(self):
        if not any(self.args.get(item) for item in ('all', 'Owner',
                                                    'RestorableBy')):
            # Default to owned snapshots and those with explicit restore perms
            self.params['Owner'] = ['self']
            owned = self.send()
            del self.params['Owner']
            self.params['RestorableBy'] = ['self']
            restorable = self.send()
            del self.params['RestorableBy']
            owned['snapshotSet'] = (owned.get('snapshotSet', []) +
                                    restorable.get('snapshotSet', []))
            return owned
        else:
            return self.send()

    def print_result(self, result):
        for snapshot in result.get('snapshotSet', []):
            self.print_snapshot(snapshot)
