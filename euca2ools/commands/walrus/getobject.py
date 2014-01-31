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
import euca2ools.bundle.pipes
from euca2ools.util import build_progressbar_label_template
import argparse
import hashlib
import os.path
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.mixins import FileTransferProgressBarMixin


class GetObject(WalrusRequest, FileTransferProgressBarMixin):
    DESCRIPTION = 'Retrieve objects from the server'
    ARGS = [Arg('--paths', metavar='BUCKET/KEY', nargs='+', route_to=None),
            Arg('--show_progress', dest='show_progress', metavar='BOOLEAN',
                default=True, route_to=None, help=argparse.SUPPRESS),
            MutuallyExclusiveArgList(
                Arg('-o', dest='opath', metavar='PATH', route_to=None,
                    help='''where to download to.  If this names an existing
                    directory or ends in '/' all objects will be downloaded
                    separately to files in that directory.  Otherwise, all
                    downloads will be written to a file with this name. Note
                    that outputting multiple objects to a file will result in
                    their concatenation.  (default: current directory)'''),
                Arg('--fileobj', metavar='FILEOBJ', route_to=None,
                    help=argparse.SUPPRESS))]

    def _download_to_fileobj(self,
                             path,
                             outfile,
                             show_progress=True,
                             pbar_label=None,
                             chunk_size=None):
        chunk_size = chunk_size or euca2ools.bundle.pipes._BUFSIZE
        bytes_written = 0
        progress_bar = None
        try:
            self.path = path
            response = self.send()
            sha1digest = hashlib.sha1()
            if show_progress:
                if 'Content-Length' in response.headers:
                    maxval = int(response.headers['Content-Length'])
                else:
                    maxval = None
                progress_bar_label = pbar_label or str(path)
                progress_bar = self.get_progressbar(label=progress_bar_label,
                                                    maxval=maxval)
                progress_bar.start()
            for chunk in response.iter_content(chunk_size=chunk_size):
                outfile.write(chunk)
                bytes_written += len(chunk)
                sha1digest.update(chunk)
                if progress_bar:
                    progress_bar.update(bytes_written)
            outfile.flush()
            if progress_bar:
                    progress_bar.finish()
        finally:
            self.log.debug('Downloaded bytes:{0} file:{1}'
                           .format(bytes_written, path))
        return sha1digest.hexdigest()

    def main(self):
        sha1_dict = {}
        opath = self.args['opath']
        paths = self.args['paths']
        show_progress = self.args.get('show_progress')
        self.log.debug('GOT SHOW PROGRESS: ' + str(show_progress))
        label = None
        if show_progress:
                label_template = build_progressbar_label_template(paths)
        if (opath) and (os.path.isdir(opath) or opath.endswith('/')):
            #Download paths to individual files under provided directory...
            if not os.path.isdir(opath):
                # Ends with '/' and does not exist -> create it
                os.mkdir(opath)
            # Download one per directory
            for index, path in enumerate(paths, 1):
                ofile_name = os.path.join(opath, path.rsplit('/', 1)[-1])
                if show_progress:
                    label = label_template.format(index=index, fname=path)
                with open(ofile_name, 'w') as ofile:
                    sha1sum = (self._download_to_fileobj(
                               path=path,
                               outfile=ofile,
                               show_progress=show_progress,
                               pbar_label=label))
                    sha1_dict[path] = sha1sum
        else:
            # Download everything to one file
            ofile = self.args.get('fileobj') or open(opath, 'w')
            try:
                for index, path in enumerate(paths, 1):
                    if show_progress:
                        label = label_template.format(index=index, fname=path)
                    sha1sum = (self._download_to_fileobj(
                               path=path,
                               outfile=ofile,
                               show_progress=show_progress,
                               pbar_label=label))
                    sha1_dict[path] = sha1sum
            finally:
                #only close the file if it was opened within this method...
                if opath and ofile:
                    ofile.close()
        return sha1_dict
