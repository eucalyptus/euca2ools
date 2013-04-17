# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2013, Eucalyptus Systems, Inc.
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

from euca2ools.commands import Euca2ools
from euca2ools.commands.walrus import Walrus
from euca2ools.commands.walrus.checkbucket import CheckBucket
from euca2ools.commands.walrus.createbucket import CreateBucket
from euca2ools.commands.walrus.putobject import PutObject
from euca2ools.exceptions import AWSError
import lxml.etree
import lxml.objectify
import os.path
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ServerError


class UploadBundle(BaseCommand):
    DESCRIPTION = 'Upload a bundle prepared by euca-bundle-image to the cloud'
    SUITE = Euca2ools
    ARGS = [Arg('-b', '--bucket', metavar='BUCKET[/PREFIX]', required=True,
                help='bucket to upload the bundle to (required)'),
            Arg('-m', '--manifest', metavar='FILE', required=True,
                help='manifest for the bundle to upload (required)'),
            MutuallyExclusiveArgList(
                Arg('--region', dest='userregion', metavar='USER@REGION',
                    help='''name of the region and/or user in config files to
                    use for connection and credential info'''),
                Arg('-U', '--url', help='storage service endpoint URL')),
            Arg('-I', '-a', '--access-key-id', '--access-key', dest='key_id',
                metavar='KEY_ID'),
            Arg('-S', '-s', '--secret-key', metavar='KEY'),
            Arg('--acl', choices=('public-read', 'aws-exec-read'),
                default='aws-exec-read', help='''canned ACL policy to apply
                to the bundle (default: aws-exec-read)'''),
            Arg('-d', '--directory', metavar='DIR',
                help='''directory that contains the bundle parts (default:
                directory that contains the manifest)'''),
            Arg('--part', metavar='INT', type=int, default=0, help='''begin
                uploading with a specific part number (default: 0)'''),
            Arg('--location', help='''location constraint of the destination
                bucket (default: inferred from s3-location-constraint in
                configuration, or otherwise none)'''),
            Arg('--retry', dest='retries', action='store_const', const=5,
                default=1, help='retry failed uploads up to 5 times'),
            Arg('--skipmanifest', action='store_true',
                help='do not upload the manifest'),
            Arg('--progress', action='store_true',
                help='show upload progress')]

    def configure(self):
        BaseCommand.configure(self)
        ## FIXME
        if self.args.get('userregion'):
            self.process_userregion(self.args['userregion'])

    def main(self):
        (bucket, __, prefix) = self.args['bucket'].partition('/')
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        full_prefix = bucket + '/' + prefix
        walrus = Walrus(userregion=self.args['userregion'],
                        url=self.args['url'], config=self.config,
                        loglevel=self.log.level)
        # First make sure the bucket exists
        try:
            req = CheckBucket(bucket=bucket, service=walrus,
                              config=self.config, key_id=self.args['key_id'],
                              secret_key=self.args['secret_key'])
            req.main()
        except AWSError as err:
            if err.status_code == 404:
                # No such bucket
                self.log.info("creating bucket '%s'", bucket)
                req = CreateBucket(bucket=bucket,
                                   location=self.args['location'],
                                   config=self.config, service=walrus,
                                   key_id=self.args['key_id'],
                                   secret_key=self.args['secret_key'])
                req.main()
            else:
                raise
        # At this point we know we can at least see the bucket, but it's still
        # possible that we can't write to it with the desired key names.  So
        # many policies are in play here that it isn't worth trying to be
        # proactive about it.

        with open(self.args['manifest']) as manifest_file:
            manifest = lxml.objectify.parse(manifest_file).getroot()

        # Now we actually upload stuff
        part_dir = (self.args.get('directory') or
                    os.path.dirname(self.args['manifest']))
        parts = {}
        for part in manifest.image.parts.part:
            parts[int(part.get('index'))] = part.filename.text
        part_paths = [os.path.join(part_dir, path) for (index, path) in
                      sorted(parts.items()) if index >= self.args['part']]
        req = PutObject(sources=part_paths, dest=full_prefix,
                        acl=self.args['acl'],
                        retries=self.args['retries'],
                        progress=self.args['progress'],
                        config=self.config, service=walrus,
                        key_id=self.args['key_id'],
                        secret_key=self.args['secret_key'])
        req.main()
        if not self.args['skipmanifest']:
            req = PutObject(sources=[self.args['manifest']],
                            dest=full_prefix, retries=self.args['retries'],
                            acl=self.args['acl'],
                            progress=self.args['progress'], config=self.config,
                            service=walrus, key_id=self.args['key_id'],
                            secret_key=self.args['secret_key'])
            req.main()
        manifest_loc = full_prefix + os.path.basename(self.args['manifest'])
        return manifest_loc

    def print_result(self, manifest_loc):
        print 'Uploaded', manifest_loc
