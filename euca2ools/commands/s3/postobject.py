# Copyright (c) 2014-2016 Hewlett Packard Enterprise Development LP
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

import argparse
import base64
import sys

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError
import six

from euca2ools.commands.argtypes import b64encoded_file_contents
from euca2ools.commands.s3 import S3Request


class PostObject(S3Request):
    DESCRIPTION = ('Upload an object to the server using an upload policy\n\n'
                   'Note that uploading a large file to a region other than '
                   'the one the bucket is may result in "Broken pipe" errors '
                   'or other connection problems that this program cannot '
                   'detect.')
    AUTH_CLASS = None
    ARGS = [Arg('source', metavar='FILE', route_to=None,
                help='file to upload (required)'),
            Arg('dest', metavar='BUCKET/KEY', route_to=None,
                help='bucket and key name to upload the object to (required)'),
            MutuallyExclusiveArgList(
                Arg('--policy', dest='Policy', metavar='POLICY',
                    type=base64.b64encode,
                    help='upload policy to use for authorization'),
                Arg('--policy-file', dest='Policy', metavar='FILE',
                    type=b64encoded_file_contents, help='''file containing the
                    upload policy to use for authorization'''))
            .required(),
            Arg('--policy-signature', dest='Signature', required=True,
                help='signature for the upload policy (required)'),
            Arg('-I', '--access-key-id', dest='AWSAccessKeyId', required=True,
                metavar='KEY_ID', help='''ID of the access key that signed the
                upload policy (required)'''),
            # --security-token is an extension meant for eucalyptus's back end
            # to use for BundleInstance operations started by the web console.
            # https://eucalyptus.atlassian.net/browse/EUCA-9911
            # https://eucalyptus.atlassian.net/browse/TOOLS-511
            Arg('--security-token', dest='x-amz-security-token',
                default=argparse.SUPPRESS, help=argparse.SUPPRESS),
            Arg('--acl', default=argparse.SUPPRESS, choices=(
                'private', 'public-read', 'public-read-write',
                'authenticated-read', 'bucket-owner-read',
                'bucket-owner-full-control', 'aws-exec-read',
                'ec2-bundle-read'), help='''the ACL the object should have
                once uploaded.  Take care to ensure this satisfies any
                restrictions the upload policy may contain.'''),
            Arg('--mime-type', dest='Content-Type', default=argparse.SUPPRESS,
                help='MIME type for the file being uploaded')]
    METHOD = 'POST'

    # noinspection PyExceptionInherit
    def configure(self):
        S3Request.configure(self)

        if self.args['source'] == '-':
            self.files['file'] = sys.stdin
        elif isinstance(self.args['source'], six.string_types):
            self.files['file'] = open(self.args['source'])
        else:
            self.files['file'] = self.args['source']
        bucket, _, key = self.args['dest'].partition('/')
        if not bucket:
            raise ArgumentError('destination bucket name must be non-empty')
        if not key:
            raise ArgumentError('destination key name must be non-empty')

    # noinspection PyExceptionInherit
    def preprocess(self):
        # FIXME:  This should really stream the contents of the source rather
        # than reading it all into memory at once, but at the moment doing so
        # would require me to write a multipart MIME encoder that supports
        # both streaming and file rewinding.  Patches that do that are very
        # welcome.
        #
        # FIXME:  While you're in there, would you mind adding progress bar
        # support?  8^)
        # pylint: disable=access-member-before-definition
        self.path, _, self.params['key'] = self.args['dest'].partition('/')
        self.body = self.params
        # pylint: enable=access-member-before-definition
        self.params = None
