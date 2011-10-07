# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
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
#
# Author: Neil Soman neil@eucalyptus.com
#         Mitch Garnaat mgarnaat@eucalyptus.com

import euca2ools.commands.eucacommand
from boto.roboto.param import Param

class DescribeSnapshots(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2010-08-31'
    Description = 'Shows information about snapshots.'
    Options = [Param(name='owner', short_name='o', long_name='owner',
                     optional=True, ptype='string',
                     doc='ID of the user who owns the snapshot.'),
               Param(name='restorable_by',
                     short_name='r', long_name='restorable-by',
                     optional=True, ptype='string',
                     doc="""restorable by (user id of the user that can
                     create volumes from the snapshot).""")]
    Args = [Param(name='snapshot', ptype='string',
                  doc='snapshots to describe',
                  cardinality='+', optional=True)]
    Filters = [Param(name='description', ptype='string',
                     doc='Description of the snapshot'),
               Param(name='owner-alias', ptype='string',
                     doc="""AWS account alias (e.g., amazon or self) or
                     AWS account ID that owns the snapshot."""),
               Param(name='owner-id', ptype='string',
                     doc='AWS account ID of the snapshot owner.'),
               Param(name='progress', ptype='string',
                     doc='The progress of the snapshot, in percentage.'),
               Param(name='snapshot-id', ptype='string',
                     doc='The ID of the snapshot.'),
               Param(name='start-time', ptype='datetime',
                     doc='Time stamp when the snapshot was initiated.'),
               Param(name='status', ptype='string',
                     doc="""Status of the snapshost.
                     Valid values: pending | completed | error."""),
               Param(name='tag-key', ptype='string',
                     doc='Key of a tag assigned to the resource.'),
               Param(name='tag-value', ptype='string',
                     doc='Value of a tag assigned to the resource.'),
               Param(name='tag:key', ptype='string',
                     doc="""Filters the results based on a specific
                     tag/value combination."""),
               Param(name='volume-id', ptype='string',
                     doc='ID of the volume the snapshot is for'),
               Param(name='volume-size', ptype='integer',
                     doc='The size of the volume, in GiB.')]
    
    def display_snapshots(self, snapshots):
        for snapshot in snapshots:
            snapshot_string = '%s\t%s\t%s\t%s\t%s' % (snapshot.id,
                    snapshot.volume_id, snapshot.status,
                    snapshot.start_time, snapshot.progress)
            print 'SNAPSHOT\t%s' % snapshot_string

    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'get_all_snapshots',
                                     snapshot_ids=self.snapshot,
                                     owner=self.owner,
                                     restorable_by=self.restorable_by)

    def main_cli(self):
        snapshots = self.main()
        self.display_snapshots(snapshots)

