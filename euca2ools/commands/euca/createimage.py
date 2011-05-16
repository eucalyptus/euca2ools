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

class CreateImage(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Creates an AMI from an EBS-based instance'
    Options = [Param(name='name', short_name='n', long_name='name',
                     optional=False, ptype='string',
                     doc='Name for the new image you are creating'),
               Param(name='description',
                     short_name='d', long_name='description',
                     optional=True, ptype='string',
                     doc='A description of the new image'),
               Param(name='no_reboot', long_name='no-reboot',
                     optional=True, ptype='boolean', default=False,
                     doc="""When set to true, the instance is not shut
                         down before creating the image. When this
                         option is used, file system integrity on
                         the created image cannot be guaranteed""")]
    Args = [Param(name='instance_id', ptype='string',
                  optional=False,
                  doc='ID of the instance')]

    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'create_image',
                                     instance_id=self.instance_id,
                                     name=self.name,
                                     description=self.description,
                                     no_reboot=self.no_reboot)

    def main_cli(self):
        image_id = self.main()
        if image_id:
            print 'IMAGE\t%s' % image_id

