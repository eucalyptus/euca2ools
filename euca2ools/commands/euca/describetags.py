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

class DescribeTags(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2010-08-31'
    Description = 'List tags associated with your account.'
    Filters = [Param(name='key', ptype='string',
                     doc='Tag key.'),
               Param(name='resource-id', ptype='string',
                     doc='Resource ID.'),
               Param(name='resource-type', ptype='string',
                     doc="""Resource type.
                     Valid Values: customer-gateway | dhcp-options | image |
                     instance | reserved-instances | snapshot |
                     spot-instances-request | subnet | volume |
                     vpc | vpn-connection | vpn-gateway"""),
               Param(name='value', ptype='string',
                     doc='Tag value.')]
    
    def display_tags(self, tags):
        for tag in tags:
            tag_string = '%s\t%s\t%s\t%s' % (tag.res_id, tag.res_type,
                                             tag.name, tag.value)
            print 'TAG\t%s' % tag_string
            
    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'get_all_tags')

    def main_cli(self):
        tags = self.main()
        self.display_tags(tags)
