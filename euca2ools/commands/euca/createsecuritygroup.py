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

class CreateSecurityGroup(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2013-06-15'
    Description = 'Creates a new security group.'
    Options = [Param(name='group_description', short_name='d',
                     long_name='description',
                     optional=False, ptype='string',
                     doc='Description for the group to be created'),
               Param(name='vpc_id', short_name='v',
                     long_name='vpc_id',
                     optional=True, ptype='string',
                     doc='vpc_id where security group to be created')]
    Args = [Param(name='group_name', ptype='string',
                  doc='unique name for the group to be created',
                  cardinality=1, optional=False)]

    def display_group(self, group):
        print 'GROUP\t%s\t%s\t%s' % (group.id, group.name, group.description)

    def main(self):
        conn = self.make_connection_cli('vpc')
        return self.make_request_cli(conn, 'create_security_group',
                                     name=self.group_name,
                                     description=self.group_description,
                                     vpc_id=self.vpc_id)

    def main_cli(self):
        group = self.main()
        self.display_group(group)
