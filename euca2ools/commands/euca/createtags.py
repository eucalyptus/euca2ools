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

class CreateTags(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2010-08-31'
    Description = """Adds or overwrites one or more tags for the
    specified resource or resources"""
    Options = [Param(name='tag', long_name='tag',
                     optional=False, ptype='string', cardinality='+',
                     doc='The key and optional value, separated by = sign.')]
    Args = [Param(name='resource_id', ptype='string',
                  doc='The resource you want to tag.',
                  cardinality='+', optional=False)]

    def main(self):
        self.tags = {}
        for tagpair in self.tag:
            t = tagpair.split('=')
            name = t[0]
            if len(t) == 1:
                value = ''
            else:
                value = t[1]
            self.tags[name] = value
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'create_tags',
                                       resource_ids=self.resource_id,
                                       tags=self.tags)

    def main_cli(self):
        status = self.main()
        if status:
            for resource_id in self.resource_id:
                for name in self.tags:
                    value = self.tags.get(name, '')
                    s = 'TAG\t%s\t%s\t%s' % (resource_id, name, value)
                    print s
