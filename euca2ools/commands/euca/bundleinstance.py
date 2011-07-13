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

import os
import euca2ools.commands.eucacommand
from boto.roboto.param import Param
import sys
import base64
from datetime import datetime, timedelta

class BundleInstance(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Bundles an S3-backed Windows instance.'
    Options = [Param(name='bucket', short_name='b', long_name='bucket',
                     optional=False, ptype='string',
                     doc='Name of the bucket to upload.'),
               Param(name='prefix', short_name='p', long_name='prefix',
                     optional=False, ptype='string', default='image',
                     doc='The prefix for the image file name'),
               Param(name='access_key_id',
                     short_name='o', long_name='user-access-key',
                     optional=False, ptype='string',
                     doc='Access Key ID of the owner of the bucket'),
               Param(name='policy', short_name='c', long_name='policy',
                    optional=True, ptype='string',
                    doc="""Base64 encoded upload policy that defines
                           upload permissions and conditions.  If no
                           policy is specified, a default policy
                           is generated.
                           NOTE: Not supported on Eucalyptus."""),
               Param(name='secret_key',
                     short_name='w', long_name='user-secret-key',
                     optional=False, ptype='string',
                     doc='Secret key used to sign the upload policy'),
               Param(name='expires', short_name='x', long_name='expires',
                     optional=False, ptype='integer', default=24,
                     doc='Expiration for the generated policy (hours).')]
    Args = [Param(name='instance_id', ptype='string',
                  doc='ID of the instance to be bundled.')]
    
    def display_bundle(self, bundle):
        bundle_string = '%s\t%s\t%s\t%s\t%s\t%s\t%s' % (bundle.id, 
                                                        bundle.instance_id,
                                                        bundle.bucket, 
                                                        bundle.prefix,
                                                        bundle.state, 
                                                        bundle.start_time,
                                                        bundle.update_time)
        print 'BUNDLE\t%s' % (bundle_string)

    def generate_default_policy(self, bucket, prefix, expiration, acl):
        delta = timedelta(hours=expiration)
        expiration_time = (datetime.utcnow() + delta).replace(microsecond=0)
        expiration_str = expiration_time.isoformat()

        policy = '{"expiration": "%s",' % expiration_str + \
        '"conditions": [' + \
        '{"bucket": "%s" },' % bucket + \
        '{"acl": "%s" },' % acl + \
        '["starts-with", "$key", "%s"]' % prefix + \
        ']' + \
        '}'
        encoded_policy = base64.b64encode(policy)
        return encoded_policy

    def main(self):
        conn = self.make_connection_cli()
        if not self.policy:
            self.policy = self.generate_default_policy(self.bucket,
                                                       self.prefix,
                                                       self.expires,
                                                       'ec2-bundle-read')
        return self.make_request_cli(conn, 'bundle_instance',
                                     instance_id=self.instance_id,
                                     s3_bucket=self.bucket,
                                     s3_prefix=self.prefix,
                                     s3_upload_policy=self.policy)

    def main_cli(self):
	bundle_task = self.main()
        self.display_bundle(bundle_task)
 
