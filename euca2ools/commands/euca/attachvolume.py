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

class AttachVolume(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Attaches an EBS volume to an instance.'
    Options = [Param(name='instance_id', short_name='i', long_name='instance',
                     optional=False, ptype='string',
                     doc="""unique id of a running instance to attach
                     the volume to."""),
               Param(name='device', short_name='d', long_name='device',
                     optional=False, ptype='string',
                     doc='local device name (inside the guest VM) to use.')]
    Args = [Param(name='volume_id', ptype='string',
                  doc='unique id for the volume to be attached',
                  cardinality=1, optional=False)]

    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'attach_volume',
                                     volume_id=self.volume_id,
                                     instance_id=self.instance_id,
                                     device=self.device)

    def main_cli(self):
        status = self.main()
        if status:
            print 'VOLUME\t%s' % self.volume_id

