# Copyright (c) 2013-2016 Hewlett Packard Enterprise Development LP
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

import hashlib
import os.path
import sys

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin
import six

from euca2ools.commands.s3 import S3Request
import euca2ools.bundle.pipes


class GetObject(S3Request, FileTransferProgressBarMixin):
    DESCRIPTION = 'Retrieve objects from the server'
    ARGS = [Arg('source', metavar='BUCKET/KEY', route_to=None,
                help='the object to download (required)'),
            Arg('-o', dest='dest', metavar='PATH', route_to=None,
                default='.', help='''where to download to.  If this names a
                directory the object will be written to a file inside of that
                directory.  If this is is "-" the object will be written to
                stdout.  Otherwise it will be written to a file with the name
                given.  (default:  current directory)''')]

    def configure(self):
        S3Request.configure(self)

        bucket, _, key = self.args['source'].partition('/')
        if not bucket:
            raise ArgumentError('source must contain a bucket name')
        if not key:
            raise ArgumentError('source must contain a key name')

        if isinstance(self.args.get('dest'), six.string_types):
            # If it is not a string we assume it is a file-like object
            if self.args['dest'] == '-':
                self.args['dest'] = sys.stdout
            elif os.path.isdir(self.args['dest']):
                basename = os.path.basename(key)
                if not basename:
                    raise ArgumentError("specify a complete file path with -o "
                                        "to download objects that end in '/'")
                dest_path = os.path.join(self.args['dest'], basename)
                self.args['dest'] = open(dest_path, 'w')
            else:
                self.args['dest'] = open(self.args['dest'], 'w')

    def preprocess(self):
        self.path = self.args['source']

    def main(self):
        # Note that this method does not close self.args['dest']
        self.preprocess()
        bytes_written = 0
        md5_digest = hashlib.md5()
        sha_digest = hashlib.sha1()
        response = self.send()
        content_length = response.headers.get('Content-Length')
        if content_length:
            pbar = self.get_progressbar(label=self.args['source'],
                                        maxval=int(content_length))
        else:
            pbar = self.get_progressbar(label=self.args['source'])
        pbar.start()
        for chunk in response.iter_content(chunk_size=euca2ools.BUFSIZE):
            self.args['dest'].write(chunk)
            bytes_written += len(chunk)
            md5_digest.update(chunk)
            sha_digest.update(chunk)
            if pbar is not None:
                pbar.update(bytes_written)
        self.args['dest'].flush()
        pbar.finish()

        # Integrity checks
        if content_length and bytes_written != int(content_length):
            self.log.error('rejecting download due to Content-Length size '
                           'mismatch (expected: %i, actual: %i)',
                           content_length, bytes_written)
            raise RuntimeError('downloaded file appears to be corrupt '
                               '(expected size: {0}, actual: {1})'
                               .format(content_length, bytes_written))
        etag = response.headers.get('ETag', '').lower().strip('"')
        if (len(etag) == 32 and
                all(char in '0123456789abcdef' for char in etag)):
            # It looks like an MD5 hash
            if md5_digest.hexdigest() != etag:
                self.log.error('rejecting download due to ETag MD5 mismatch '
                               '(expected: %s, actual: %s)',
                               etag, md5_digest.hexdigest())
                raise RuntimeError('downloaded file appears to be corrupt '
                                   '(expected MD5: {0}, actual: {1})'
                                   .format(etag, md5_digest.hexdigest()))

        return {self.args['source']: {'md5': md5_digest.hexdigest(),
                                      'sha1': sha_digest.hexdigest(),
                                      'size': bytes_written}}
