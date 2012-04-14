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

class DescribeBundleTasks(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2010-08-31'
    Description = 'Retrieves previously submitted bundle tasks.'
    Args = [Param(name='bundle_id', ptype='string',
                  doc="""Identifiers of bundle tasks to describe.
                  If no bundle task ids are specified
                  all bundle tasks are returned.""",
                  cardinality='+', optional=True)]
    Filters = [Param(name='bundle-id', ptype='string',
                     doc='ID of the bundle task.'),
               Param(name='error-code', ptype='string',
                     doc='If the task failed, the error code returned'),
               Param(name='error-message', ptype='string',
                     doc='If the task failed, the error message returned.'),
               Param(name='instance-id', ptype='string',
                     doc='ID of the instance that was bundled.'),
               Param(name='progress', ptype='string',
                     doc='Level of task completion, in percent (e.g., 20%).'),
               Param(name='s3-bucket', ptype='string',
                     doc='bucket where the AMI will be stored'),
               Param(name='s3-prefix', ptype='string',
                     doc='Beginning of the AMI name.'),
               Param(name='start-time', ptype='string',
                     doc='Time the task started.'),
               Param(name='state', ptype='string',
                     doc='State of the task.'),
               Param(name='update-time', ptype='string',
                     doc='Time of the most recent update for the task.')]
    
    def display_bundles(self, bundles):
        for bundle in bundles:
            bundle_string = '%s\t%s\t%s\t%s\t%s\t%s\t%s' % (
                bundle.id,
                bundle.instance_id,
                bundle.bucket,
                bundle.prefix,
                bundle.state,
                bundle.start_time,
                bundle.update_time)
            print 'BUNDLE\t%s' % bundle_string

    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'get_all_bundle_tasks',
                                     bundle_ids=self.bundle_id)

    def main_cli(self):
        bundles = self.main()
        self.display_bundles(bundles)


