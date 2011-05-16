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
import euca2ools.bundler
from boto.roboto.param import Param

class GetPassword(euca2ools.commands.eucacommand.EucaCommand):

    Description = """Retrieves decrypts the administrator password
    for a Windows instance."""
    Options = [Param(name='privatekey',
                     short_name='k', long_name='priv-launch-key',
                     ptype='file', optional=False,
                     doc="""The file that contains the private key
                     used to launch the instance.""")]
    Args = [Param(name='instance_id', ptype='string', optional=False,
                     doc='unique identifier for the Windows instance')]

    def main(self):
        conn = self.make_connection_cli()
        pd = self.make_request_cli(conn, 'get_password_data',
                                   instance_id=self.instance_id)
        if pd:
            # TODO - this is actually in the bundler
            # TODO validate file?
 	    return euca2ools.bundler.Bundler(self).decrypt_string(pd, self.privatekey, encoded=True)

    def main_cli(self):
        pw = self.main()
        print pw

