# Copyright 2013-2014 Eucalyptus Systems, Inc.
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
import hashlib
import socket
import sys
import threading
import time

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError, ClientError
from requestbuilder.mixins import FileTransferProgressBarMixin

from euca2ools.commands.s3 import S3Request
import euca2ools.util


class PutObject(S3Request, FileTransferProgressBarMixin):
    DESCRIPTION = ('Upload an object to the server\n\nNote that uploading a '
                   'large file to a region other than the one the bucket is '
                   'may result in "Broken pipe" errors or other connection '
                   'problems that this program cannot detect.')
    ARGS = [Arg('source', metavar='FILE', route_to=None,
                help='file to upload (required)'),
            Arg('dest', metavar='BUCKET/KEY', route_to=None,
                help='bucket and key name to upload the object to (required)'),
            Arg('--size', type=int, route_to=None, help='''the number of
                bytes to upload (required when reading from stdin)'''),
            Arg('--acl', route_to=None, choices=(
                'private', 'public-read', 'public-read-write',
                'authenticated-read', 'bucket-owner-read',
                'bucket-owner-full-control', 'aws-exec-read')),
            Arg('--mime-type', route_to=None,
                help='MIME type for the file being uploaded'),
            Arg('--retry', dest='retries', action='store_const', const=5,
                default=0, route_to=None,
                help='retry interrupted uploads up to 5 times'),
            Arg('--progressbar-label', help=argparse.SUPPRESS)]
    METHOD = 'PUT'

    def __init__(self, **kwargs):
        S3Request.__init__(self, **kwargs)
        self.last_upload_error = None
        self._lock = threading.Lock()

    # noinspection PyExceptionInherit
    def configure(self):
        S3Request.configure(self)
        if self.args['source'] == '-':
            if self.args.get('size') is None:
                raise ArgumentError(
                    "argument --size is required when uploading stdin")
            source = _FileObjectExtent(sys.stdin, self.args['size'])
        elif isinstance(self.args['source'], basestring):
            source = _FileObjectExtent.from_filename(
                self.args['source'], size=self.args.get('size'))
        else:
            if self.args.get('size') is None:
                raise ArgumentError(
                    "argument --size is required when uploading a file object")
            source = _FileObjectExtent(self.args['source'], self.args['size'])
        self.args['source'] = source
        bucket, _, key = self.args['dest'].partition('/')
        if not bucket:
            raise ArgumentError('destination bucket name must be non-empty')
        if not key:
            raise ArgumentError('destination key name must be non-empty')

    def preprocess(self):
        self.path = self.args['dest']
        if self.args.get('acl'):
            self.headers['x-amz-acl'] = self.args['acl']
        if self.args.get('mime_type'):
            self.headers['Content-Type'] = self.args['mime_type']

    # noinspection PyExceptionInherit
    def main(self):
        self.preprocess()
        source = self.args['source']
        self.headers['Content-Length'] = source.size

        # We do the upload in another thread so the main thread can show a
        # progress bar.
        upload_thread = threading.Thread(
            target=self.try_send, args=(source,),
            kwargs={'retries_left': self.args.get('retries') or 0})
        # The upload thread is daemonic so ^C will kill the program more
        # cleanly.
        upload_thread.daemon = True
        upload_thread.start()
        pbar_label = self.args.get('progressbar_label') or source.filename
        pbar = self.get_progressbar(label=pbar_label, maxval=source.size)
        pbar.start()
        while upload_thread.is_alive():
            pbar.update(source.tell())
            time.sleep(0.05)
        pbar.finish()
        upload_thread.join()
        source.close()
        with self._lock:
            if self.last_upload_error is not None:
                # pylint: disable=E0702
                raise self.last_upload_error
                # pylint: enable=E0702

    def try_send(self, source, retries_left=0):
        self.body = source
        if retries_left > 0 and not source.can_rewind:
            self.log.warn('source cannot rewind, so requested retries will '
                          'not be attempted')
            retries_left = 0
        try:
            response = self.send()
            our_md5 = source.read_hexdigest
            their_md5 = response.headers['ETag'].lower().strip('"')
            if their_md5 != our_md5:
                self.log.error('corrupt upload (our MD5: %s, their MD5: %s',
                               our_md5, their_md5)
                raise ClientError('upload was corrupted during transit')
        except ClientError as err:
            if len(err.args) > 0 and isinstance(err.args[0], socket.error):
                self.log.warn('socket error')
                if retries_left > 0:
                    self.log.info('retrying upload (%i retries remaining)',
                                  retries_left)
                    source.rewind()
                    return self.try_send(source, retries_left - 1)
            with self._lock:
                self.last_upload_error = err
            raise
        except Exception as err:
            with self._lock:
                self.last_upload_error = err
            raise


class _FileObjectExtent(object):
    # By rights this class should be iterable, but if we do that then requests
    # will attempt to use chunked transfer-encoding, which S3 does not
    # support.

    def __init__(self, fileobj, size, filename=None):
        self.closed = False
        self.filename = filename
        self.fileobj = fileobj
        self.size = size
        self.__bytes_read = 0
        self.__md5 = hashlib.md5()
        if hasattr(self.fileobj, 'tell'):
            self.__initial_pos = self.fileobj.tell()
        else:
            self.__initial_pos = None

    def __len__(self):
        return self.size

    @classmethod
    def from_filename(cls, filename, size=None):
        if size is None:
            size = euca2ools.util.get_filesize(filename)
        return cls(open(filename), size, filename=filename)

    @property
    def can_rewind(self):
        return hasattr(self.fileobj, 'seek') and self.__initial_pos is not None

    def close(self):
        self.fileobj.close()
        self.closed = True

    def next(self):
        remaining = self.size - self.__bytes_read
        if remaining <= 0:
            raise StopIteration()
        chunk = self.fileobj.next()  # might raise StopIteration, which is good
        chunk = chunk[:remaining]  # throw away data that are off the end
        self.__bytes_read += len(chunk)
        self.__md5.update(chunk)
        return chunk

    def read(self, size=-1):
        remaining = self.size - self.__bytes_read
        if size < 0:
            chunk_len = remaining
        else:
            chunk_len = min(remaining, size)
        chunk = self.fileobj.read(chunk_len)
        self.__bytes_read += len(chunk)
        self.__md5.update(chunk)
        return chunk

    @property
    def read_hexdigest(self):
        return self.__md5.hexdigest()

    def rewind(self):
        if not hasattr(self.fileobj, 'seek'):
            raise TypeError('file object is not seekable')
        assert self.__initial_pos is not None
        self.fileobj.seek(self.__initial_pos)
        self.__bytes_read = 0
        self.__md5 = hashlib.md5()

    def tell(self):
        return self.__bytes_read
