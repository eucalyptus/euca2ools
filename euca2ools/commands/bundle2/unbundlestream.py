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

from euca2ools.commands import Euca2ools
import euca2ools.bundle.pipes
from euca2ools.bundle.pipes.core import create_unbundle_pipeline
from euca2ools.bundle.util import open_pipe_fileobjs, spawn_process, \
    close_all_fds, waitpid_in_thread
from shutil import copyfileobj
import os
import argparse
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.util import set_userregion
from requestbuilder.mixins import FileTransferProgressBarMixin


class UnbundleStream(BaseCommand, FileTransferProgressBarMixin):
    DESCRIPTION = ('Recreate an image from a source bundle stream\n\nThe key used '
                   'to unbundle the image must match the certificate that was '
                   'used to bundle it.')
    SUITE = Euca2ools
    ARGS = [
        Arg('-s', '--source', metavar='INFILE', default=None,
            help=argparse.SUPPRESS),
        Arg('-d', '--destination', metavar='OUTFILE', required=True,
            help='Destination path to write file to. Use "-" to write to <stdout>'),
        Arg('-k', '--privatekey', metavar='FILE', required=True,
            help='''file containing the private key to decrypt the bundle
                with.  This must match the certificate used when bundling the
                image.'''),
        Arg('-e', '--enc-key', dest='enc_key', required=True,
            help='''Key used to decrypt bundled image'''),
        Arg('-v', '--enc-iv', dest='enc_iv', required=True,
            help='''Initialization vector used to decrypt bundled image'''),
        Arg('--maxbytes', dest='maxbytes', metavar='MAX BYTES', default=0,
            help='''The Maximum bytes allowed to be written to the
                destination.'''),
        Arg('--progressbar', dest='progressbar', help=argparse.SUPPRESS)]

    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)
        #self.configure()
        set_userregion(self.config, self.args.get('userregion'))
        set_userregion(self.config, os.getenv('EUCA_REGION'))

        #Get the mandatory private key...
        if not self.args.get('privatekey'):
            config_privatekey = self.config.get_user_option('private-key')
            if self.args.get('userregion'):
                self.args['privatekey'] = config_privatekey
            elif 'EC2_PRIVATE_KEY' in os.environ:
                self.args['privatekey'] = os.getenv('EC2_PRIVATE_KEY')
            elif config_privatekey:
                self.args['privatekey'] = config_privatekey
            else:
                raise ArgumentError(
                    'missing private key; please supply one with -k')
        self.args['privatekey'] = os.path.expanduser(os.path.expandvars(
            self.args['privatekey']))
        if not os.path.exists(self.args['privatekey']):
            raise ArgumentError("private key file '{0}' does not exist"
            .format(self.args['privatekey']))
        if not os.path.isfile(self.args['privatekey']):
            raise ArgumentError("private key file '{0}' is not a file"
            .format(self.args['privatekey']))

        #Get optional destination directory...
        dest_dir = self.args['destination']
        if not isinstance(dest_dir, file) and not (dest_dir == "-"):
            dest_dir = os.path.expanduser(os.path.abspath(dest_dir))
            if not os.path.exists(dest_dir):
                raise ArgumentError("Destination directory '{0}' does not exist"
                .format(dest_dir))
            if not os.path.isdir(dest_dir):
                raise ArgumentError("Destination '{0}' is not Directory"
                .format(dest_dir))
        self.args['destination'] = dest_dir

    def _write_inputfile_to_pipe(self, infile, outfile, debug=False):
        """
        Intended for reading from file 'infile' and writing to pipe via 'outfile'.
        :param outfile: file obj used for writing infile to
        :param infile: file obj used for reading input from to feed pipe at 'outfile'
        """
        self.log.debug('Starting _write_file_to_pipe...')
        self.log.debug('write_file_to_pipe using input file:' + str(infile))
        self.log.debug('write_file_to_pipe using output file:' + str(outfile))
        close_all_fds([infile, outfile])
        try:
            copyfileobj(infile, outfile, length=euca2ools.bundle.pipes._BUFSIZE)
        except IOError as ioe:
            # HACK
            self.log.debug('IO Error in write_file_to_pipe:' + str(ioe))
            if not debug:
                return
            raise
        finally:
            self.log.debug('Done, closing write end of pipe after writing')
            infile.close()
            outfile.close()

    def main(self):
        pbar = self.args.get('progressbar', None)

        #todo Should this only write to fileobj or stdout, and not a local path?
        #Setup the destination fileobj...
        if isinstance(self.args.get('destination'), file):
            #Use provided file obj...
            dest_file = self.args.get('destination')
        elif self.args.get('destination') == '-':
            #Use stdout...
            dest_file = os.fdopen(os.dup(os.sys.stdout.fileno()), 'w')
        else:
            #Open file at path provided...
            dest_file = open(self.args.get('destination'), 'w')

        #Start the unbundle...
        try:
            if self.args.get('source'):
                #Let caller feed pipe from file obj provided...
                digest = create_unbundle_pipeline(infile=self.args.get('source'),
                                                  outfile=dest_file,
                                                  enc_key=self.args.get('enc_key'),
                                                  enc_iv=self.args.get('enc_iv'),
                                                  progressbar=pbar,
                                                  debug=self.args.get('debug'),
                                                  maxbytes=int(self.args['maxbytes']))
            else:
                #Unbundle from stdin stream...
                unbundle_r, unbundle_w = open_pipe_fileobjs()
                writer = spawn_process(self._write_inputfile_to_pipe,
                                       infile=os.fdopen(os.dup(os.sys.stdin.fileno())),
                                       outfile=unbundle_w,
                                       debug=self.args.get('debug'))
                unbundle_w.close()
                waitpid_in_thread(writer.pid)
                digest = create_unbundle_pipeline(infile=unbundle_r,
                                                  outfile=dest_file,
                                                  enc_key=self.args.get('enc_key'),
                                                  enc_iv=self.args.get('enc_iv'),
                                                  progressbar=pbar,
                                                  debug=self.args.get('debug'),
                                                  maxbytes=int(self.args['maxbytes']))
            digest = digest.strip()
            self.log.debug('Digest for unbundled image:' + str(digest))
        except KeyboardInterrupt:
            print 'Caught keyboard interrupt'
            return
        return digest

    def print_result(self, result):
        if result and self.args.get('debug'):
            print 'Finished unbundle stream. ', result


if __name__ == '__main__':
    UnbundleStream.run()