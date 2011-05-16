# Software License Agreement (BSD License)
#
# Copyright (c) 20092011, Eucalyptus Systems, Inc.
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

class ResetImageAttribute(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Reset attributes of an image.'
    Options = [Param(name='launchPermission', metavar='launch_permission',
                     short_name='l', long_name='launch-permission',
                     optional=True, ptype='boolean',
                     doc='show launch permissions.')]
    Args = [Param(name='image_id', ptype='string',
                  doc="""unique identifier for the image that you want
                  to reset the attributes for.""",
                  cardinality=1, optional=False)]
    
    def main(self):
        attribute = None
        attr_names = [ opt.name for opt in self.Options ]
        for name in attr_names:
            if not attribute:
                if getattr(self, name):
                    attribute = name
        if attribute:
            conn = self.make_connection_cli()
            return self.make_request_cli(conn, 'reset_image_attribute',
                                         image_id=self.image_id,
                                         attribute=attribute)
        else:
            msg = 'image attribute must be specified'
            self.display_error_and_exit(msg)

    def main_cli(self):
        status = self.main()
        if status:
            print 'IMAGE\t%s' % self.image_id
        
