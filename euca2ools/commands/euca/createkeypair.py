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
from os import chmod
from stat import *

class CreateKeyPair(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Creates a new key pair for use with instances'
    Options = [Param(name='filename', short_name='f',
                  long_name='filename', ptype='string',
                  doc='Filename to save the private key to. Default ' +
                  'action is to overwite the file.',
                  optional=True)]

    Args = [Param(name='keypair_name', ptype='string',
                  doc='unique name for a keypair to be created',
                  cardinality=1, optional=False)]

    def display_fingerprint(self, keypair):
        print 'KEYPAIR\t%s\t%s' % (keypair.name, keypair.fingerprint)

    def display_keypair(self, keypair):
        print keypair.material

    def save_keypair_to_file(self, keypair):
        keyfile = open(self.filename, 'w')
        keyfile.write(keypair.material)
        keyfile.close()

        chmod(self.filename, S_IRUSR|S_IWUSR)

    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'create_key_pair',
                                     key_name=self.keypair_name)

    def main_cli(self):
        keypair = self.main()
        self.display_fingerprint(keypair)
        if self.filename != None:
            self.save_keypair_to_file(keypair)
        else:
            self.display_keypair(keypair)
