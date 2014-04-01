# Copyright 2009-2013 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from requestbuilder import Arg

from euca2ools.commands.bundle.mixins import BundleDownloadingMixin
from euca2ools.commands.s3 import S3Request
from euca2ools.commands.s3.deletebucket import DeleteBucket
from euca2ools.commands.s3.deleteobject import DeleteObject


class DeleteBundle(S3Request, BundleDownloadingMixin):
    DESCRIPTION = 'Delete a previously-uploaded bundle'
    ARGS = [Arg('--clear', dest='clear', action='store_true',
                help='attempt to delete the bucket as well')]

    def main(self):
        manifest = self.fetch_manifest(self.service)
        for part, part_s3path in self.map_bundle_parts_to_s3paths(manifest):
            req = DeleteObject(config=self.config, service=self.service,
                               path=part_s3path)
            req.main()
            print '>>>', part, part_s3path
        manifest_s3path = self.get_manifest_s3path()
        if manifest_s3path:
            req = DeleteObject(config=self.config, service=self.service,
                               path=manifest_s3path)
            req.main()
            print '>>> manifest', manifest_s3path

        if self.args.get('clear'):
            req = DeleteBucket(service=self.service, config=self.config,
                               bucket=self.args['bucket'].split('/')[0])
            req.main()
            print '>>> bucket', self.args['bucket'].split('/')[0]
