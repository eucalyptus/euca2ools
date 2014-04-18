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
from requestbuilder.exceptions import ServerError

from euca2ools.commands.bundle.mixins import BundleDownloadingMixin
from euca2ools.commands.s3 import S3Request
from euca2ools.commands.s3.deletebucket import DeleteBucket
from euca2ools.commands.s3.deleteobject import DeleteObject


class DeleteBundle(S3Request, BundleDownloadingMixin):
    DESCRIPTION = 'Delete a previously-uploaded bundle'
    ARGS = [Arg('--clear', dest='clear', action='store_true',
                help='attempt to delete the bucket as well')]

    def main(self):
        try:
            manifest = self.fetch_manifest(self.service)
        except ServerError as err:
            if err.status_code == 404 and self.args.get('clear'):
                try:
                    # We are supposed to try to delete the bucket even
                    # if the manifest isn't there.  If it works, the
                    # bundle is also gone and we can safely return.
                    #
                    # https://eucalyptus.atlassian.net/browse/TOOLS-379
                    self.__delete_bucket()
                    return
                except ServerError:
                    # If the bucket wasn't empty then we'll go back to
                    # complaining about the missing manifest.
                    self.log.error(
                        'failed to delete bucket %s after a failed '
                        'attempt to fetch the bundle manifest',
                        bucket=self.args['bucket'].split('/')[0],
                        exc_info=True)
            raise

        for _, part_s3path in self.map_bundle_parts_to_s3paths(manifest):
            req = DeleteObject.from_other(self, path=part_s3path)
            req.main()
        manifest_s3path = self.get_manifest_s3path()
        if manifest_s3path:
            req = DeleteObject.from_other(self, path=manifest_s3path)
            req.main()

        if self.args.get('clear'):
            self.__delete_bucket()

    def __delete_bucket(self):
        req = DeleteBucket.from_other(self,
                                      bucket=self.args['bucket'].split('/')[0])
        req.main()
