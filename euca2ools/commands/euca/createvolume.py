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

class CreateVolume(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Creates a volume in a specified availability zone.'
    Options = [Param(name='size', short_name='s', long_name='size',
                     optional=True, ptype='integer',
                     doc='size of the volume (in GiB).'),
               Param(name='snapshot', long_name='snapshot',
                     optional=True, ptype='string',
                     doc="""snapshot id to create the volume from.
                     Either size or snapshot can be specified (not both)."""),
               Param(name='zone', short_name='z', long_name='zone',
                     optional=False, ptype='string',
                     doc='availability zone to create the volume in')]

    def display_volume(self, volume):
        if not volume.id:
            return
        volume_string = '%s' % volume.id
        if volume.size:
            volume_string += '\t%d' % volume.size
        if volume.snapshot_id:
            volume_string += '\t%s' % volume.snapshot_id
        volume_string += '\t%s\t%s' % (volume.status, volume.create_time)
        print 'VOLUME\t%s' % volume_string

    def main(self):
        if (self.size or self.snapshot) and self.zone:
            conn = self.make_connection_cli()
            return self.make_request_cli(conn, 'create_volume',
                                         size=self.size, zone=self.zone,
                                         snapshot=self.snapshot)
        else:
            msg = 'Either size or snapshot_id must be specified'
            self.display_error_and_exit(msg)

    def main_cli(self):
        volume = self.main()
        if volume:
            self.display_volume(volume)

