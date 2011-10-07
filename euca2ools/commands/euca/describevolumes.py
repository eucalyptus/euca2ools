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

class DescribeVolumes(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2010-08-31'
    Description = 'Shows information about volumes.'
    Args = [Param(name='volume_id', ptype='string',
                  doc='volumes to describe',
                  cardinality='+', optional=True)]
    Filters = [Param(name='attachment.attach-time', ptype='string',
                     doc='Time stamp when the attachment initiated.'),
               Param(name='attachment.delete-on-termination', ptype='string',
                     doc="""Whether the volume will be deleted on
                     instance termination."""),
               Param(name='attachment.device', ptype='string',
                     doc="""How the volume is exposed to the
                     instance (e.g., /dev/sda1)."""),
               Param(name='attachment.instance-id', ptype='string',
                     doc='ID of the instance the volume is attached to.'),
               Param(name='attachment.status', ptype='datetime',
                     doc="""Attachment state.
                     Valid Values: attaching | attached | detaching | detached"""),
               Param(name='availability-zone', ptype='string',
                     doc='Availability Zone in which the volume was created.'),
               Param(name='create-time', ptype='datetime',
                     doc='Time stamp when the volume was created.'),
               Param(name='size', ptype='integer',
                     doc='Size of the volume, in GiB (e.g., 20).'),
               Param(name='snapshot-id', ptype='string',
                     doc='Snapshot from which the volume was created.'),
               Param(name='status', ptype='string',
                     doc="""Status of the volume.
                     Valid values: pending | completed | error."""),
               Param(name='tag-key', ptype='string',
                     doc='Key of a tag assigned to the resource.'),
               Param(name='tag-value', ptype='string',
                     doc='Value of a tag assigned to the resource.'),
               Param(name='tag:key', ptype='string',
                     doc="""Filters the results based on a specific
                     tag/value combination."""),
               Param(name='volume-id', ptype='string',
                     doc='ID of the volume the snapshot is for')]
    
    def display_volumes(self, volumes):
        for volume in volumes:
            volume_string = '%s\t ' % volume.id
            if volume.size:
                volume_string += '%d' % volume.size
            if volume.snapshot_id:
                volume_string += '\t%s' % volume.snapshot_id
            else:
                volume_string += '\t'

            az = getattr(volume, 'availabilityZone', object)
            if az is object:
                az = volume.zone
            if az:
                volume_string += '\t%s' % az

            volume_string += '\t%s\t%s' % (volume.status,
                    volume.create_time)
            print 'VOLUME\t%s' % volume_string
            if volume.status == 'in-use':
                attachment_string = '%s\t%s\t%s\t%s' % (volume.id,
                        volume.attach_data.instance_id,
                        volume.attach_data.device,
                        volume.attach_data.attach_time)
                print 'ATTACHMENT\t%s' % attachment_string

    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'get_all_volumes',
                                     volume_ids=self.volume_id)

    def main_cli(self):
        volumes = self.main()
        self.display_volumes(volumes)

