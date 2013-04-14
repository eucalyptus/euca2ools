# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
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

import datetime
from euca2ools.commands.walrus import WalrusRequest
import mimetypes
import os.path
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError, ClientError
import socket
import sys
import threading
import time


class PutObject(WalrusRequest):
    DESCRIPTION = 'Upload objects to the server'
    ARGS = [Arg('sources', metavar='FILE', nargs='+', route_to=None,
                help='file(s) to upload'),
            Arg('dest', metavar='BUCKET/PREFIX', route_to=None,
                help='bucket name and optional prefix for key names'),
            Arg('-T', dest='literal_dest', action='store_true', route_to=None,
                help='''treat the destination as the full bucket and key name
                for the uploaded object instead of a bucket and prefix.  This
                only works when uploading a single file.'''),
            Arg('--guess-mime-type', action='store_true', route_to=None,
                help='''automatically select MIME types for the files being
                uploaded'''),
            Arg('--progress', action='store_true', route_to=None,
                help='show upload progress')]
    METHOD = 'PUT'

    def configure(self):
        WalrusRequest.configure(self)
        if self.args['literal_dest'] and len(self.args['sources']) != 1:
            raise ArgumentError('argument -T: only allowed with one file')
        if self.args['dest'].startswith('/'):
            raise ArgumentError('destination must begin with a bucket name')

    def main(self):
        max_source_len = max(len(os.path.basename(source)) for source
                             in self.args['sources'])
        for source_filename in self.args['sources']:
            if self.args['literal_dest']:
                (bucket, __, keyname) = self.args['dest'].partition('/')
                if not keyname:
                    raise ArgumentError('destination must contain a key name')
            else:
                (bucket, __, prefix) = self.args['dest'].partition('/')
                keyname = prefix + os.path.basename(source_filename)
            self.path = bucket + '/' + keyname
            self.headers['Content-Length'] = os.path.getsize(source_filename)
            self.headers.pop('Content-Type', None)
            if self.args['guess_mime_type']:
                mtype = mimetypes.guess_type(source_filename)
                if mtype:
                    self.headers['Content-Type'] = mtype

            self.log.info('uploading %s to %s', source_filename, self.path)
            with open(source_filename) as source:
                upload_thread = threading.Thread(target=self.try_send,
                                                 args=(source,))
                # The upload thread is daemonic so ^C will kill the program
                # more cleanly.
                upload_thread.daemon = True
                upload_thread.start()
                if self.args['progress']:
                    import progressbar
                    filename_padding = ' ' * (max_source_len -
                                              len(source_filename))
                    widgets = [os.path.basename(source_filename),
                               filename_padding, ' ', progressbar.Percentage(),
                               ' ', progressbar.Bar(marker='='), ' ',
                               progressbar.FileTransferSpeed(), ' ',
                               progressbar.AdaptiveETA()]
                    bar = progressbar.ProgressBar(
                        maxval=os.path.getsize(source_filename),
                        widgets=widgets)
                    bar.start()
                    while upload_thread.is_alive():
                        bar.update(source.tell())
                        time.sleep(0.01)
                    bar.finish()
                else:
                    # If we don't at least do *something* in the main thread
                    # then attempts to kill the program with ^C will only be
                    # handled when the current upload completes, which could
                    # be minutes away or even longer.
                    while upload_thread.is_alive():
                        time.sleep(0.01)
                upload_thread.join()

    def try_send(self, source):
        self.body = source
        try:
            self.send()
        except ClientError as err:
            # When you start uploading something to the wrong region S3 will
            # try to send an error response, but requests doesn't listen for
            # that until it's done uploading the whole file.  If the file takes
            # more than a couple seconds to upload then S3 will kill the
            # connection before then, leaving us with a broken pipe and a
            # ConnectionError from requests, but no error response.
            #
            # We should be using Expect: 100-continue so we can deal with that
            # before we send anything, but requests doesn't support that and
            # it isn't trivial to implement from outside.
            # (See https://github.com/kennethreitz/requests/issues/713)
            #
            # Plan C is to retry the bad request with something small emough to
            # give us the contents of the error and then retry with the URL
            # that that error contains.
            if len(err.args) > 0 and isinstance(err.args[0], socket.error):
                self.log.warn('upload interrupted by socket error')
                self.log.debug('retrieving error message from server')
                self.headers['Content-Length'] = 0
                self.body = ''
                self.saved_body = source
                self.send()
            else:
                raise

    def handle_server_error(self, err):
        if (300 <= err.status_code < 400 and 'Endpoint' in err.elements and
            hasattr(self, 'saved_body')):
            # This was a redirect-probing request; restore the original body to
            # make the usual redirect handling work
            print >> sys.stderr, 'retrying upload with endpoint', \
                err.elements['Endpoint']
            self.body = self.saved_body
            del self.saved_body
            self.headers['Content-Length'] = os.path.getsize(self.body.name)
        return WalrusRequest.handle_server_error(self, err)
