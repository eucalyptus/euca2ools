# Copyright 2013 Eucalyptus Systems, Inc.
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

from euca2ools.commands.walrus import WalrusRequest
from euca2ools.util import build_progressbar_label_template
import os.path
from requestbuilder import Arg
from requestbuilder.mixins import FileTransferProgressBarMixin


class GetObject(WalrusRequest, FileTransferProgressBarMixin):
    DESCRIPTION = 'Retrieve objects from the server'
    ARGS = [Arg('paths', metavar='BUCKET/KEY', nargs='+', route_to=None),
            Arg('-o', dest='opath', metavar='PATH', default='.', route_to=None,
                help='''where to download to.  If this names an existing
                directory or ends in '/' all objects will be downloaded
                separately to files in that directory.  Otherwise, all
                downloads will be written to a file with this name.  Note that
                outputting multiple objects to a file will result in their
                concatenation.  (default: current directory)''')]

    def main(self):
        opath = self.args['opath']
        label_template = build_progressbar_label_template(self.args['paths'])
        if opath.endswith('/') and not os.path.isdir(opath):
            # Ends with '/' and does not exist -> create it
            os.mkdir(opath)
        if os.path.isdir(opath):
            # Download one per directory
            for index, path in enumerate(self.args['paths'], 1):
                ofile_name = os.path.join(opath, path.rsplit('/', 1)[-1])
                self.path = path
                response = self.send()
                if 'Content-Length' in response.headers:
                    maxval = int(response.headers['Content-Length'])
                else:
                    maxval = None
                label = label_template.format(index=index, fname=path)
                pbar = self.get_progressbar(label=label, maxval=maxval)
                pbar.start()
                with open(ofile_name, 'w') as ofile:
                    for chunk in response.iter_content(chunk_size=16384):
                        ofile.write(chunk)
                        pbar.update(ofile.tell())
                    ofile.flush()
                    pbar.finish()
        else:
            # Download everything to one file
            with open(opath, 'w') as ofile:
                for index, path in enumerate(self.args['paths'], 1):
                    self.path = path
                    response = self.send()
                    bytes_written = 0
                    if 'Content-Length' in response.headers:
                        maxval = int(response.headers['Content-Length'])
                    else:
                        maxval = None
                    label = label_template.format(index=index, fname=path)
                    pbar = self.get_progressbar(label=label, maxval=maxval)
                    pbar.start()
                    for chunk in response.iter_content(chunk_size=16384):
                        ofile.write(chunk)
                        bytes_written += len(chunk)
                        pbar.update(bytes_written)
                    pbar.finish()
                ofile.flush()
