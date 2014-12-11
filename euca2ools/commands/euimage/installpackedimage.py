# (C) Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import contextlib
import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile

from requestbuilder import Arg
from requestbuilder.auth import QuerySigV2Auth
from requestbuilder.mixins import FileTransferProgressBarMixin, TabifyingMixin

import euca2ools
from euca2ools.bundle.util import open_pipe_fileobjs
from euca2ools.commands.ec2 import EC2
from euca2ools.commands.euimage import (IMAGE_ARCNAME, IMAGE_MD_ARCNAME,
                                        PACK_MD_ARCNAME)
from euca2ools.commands.euimage.metadata import (ImagePackMetadata,
                                                 ImageMetadata)
from euca2ools.commands.s3 import S3Request


class InstallPackedImage(S3Request, FileTransferProgressBarMixin,
                         TabifyingMixin):
    DESCRIPTION = '***TECH PREVIEW***\n\nInstall a packed image into the cloud'
    ARGS = [Arg('pack_filename', metavar='FILE',
                help='the pack to install (required)'),
            Arg('--profile', help='''which of the image's profiles to
                install (default: "default")'''),
            # Upload stuff (for bundle pieces or imported disk image pieces)
            Arg('-b', '--bucket', metavar='BUCKET[/PREFIX]',
                help='bucket to upload the image to (required)'),
            Arg('--location', help='''location constraint of the destination
                bucket (default: inferred from s3-location-constraint in
                configuration, or otherwise none'''),
            # Bundle stuff
            Arg('--privatekey', metavar='FILE', help='''file containing
                your private key to sign the bundle's manifest with.  This
                private key will also be required to unbundle the bundle in
                the future.  (instance-store only)'''),
            Arg('--cert', metavar='FILE', help='''file containing your
                X.509 certificate (instance-store only)'''),
            Arg('--ec2cert', metavar='FILE', help='''file containing the
                cloud's X.509 certificate (instance-store only)'''),
            Arg('--user', metavar='ACCOUNT',
                help='your account ID (instance-store only)'),
            # Registration stuff
            Arg('--kernel', metavar='IMAGE', help='''ID of the kernel image to
                associate with this machine image (paravirtual only)'''),
            Arg('--ramdisk', metavar='IMAGE', help='''ID of the ramdisk image
                to associate with this machine image (paravirtual only)'''),
            Arg('--ec2-url', help='compute service endpoint URL'),
            Arg('--ec2-auth', help=argparse.SUPPRESS),
            Arg('--ec2-service', help=argparse.SUPPRESS)]

    def configure(self):
        S3Request.configure(self)
        if not self.args.get('ec2_service'):
            self.args['ec2_service'] = EC2.from_other(
                self.service, url=self.args.get('ec2_url'))

        if not self.args.get('ec2_auth'):
            self.args['ec2_auth'] = QuerySigV2Auth.from_other(self.auth)
        if not self.args.get('profile'):
            self.args['profile'] = 'default'

    def main(self):
        services = {'s3': {'service': self.service, 'auth': self.auth},
                    'ec2': {'service': self.args['ec2_service'],
                            'auth': self.args['ec2_auth']}}
        decompressed_image = tempfile.TemporaryFile()
        with contextlib.closing(tarfile.open(name=self.args['pack_filename'],
                                             mode='r')) as pack:
            member = pack.getmember(PACK_MD_ARCNAME)
            with contextlib.closing(pack.extractfile(member)) as md_file:
                pack_md = ImagePackMetadata.from_fileobj(md_file)
            member = pack.getmember(IMAGE_MD_ARCNAME)
            with contextlib.closing(pack.extractfile(member)) as md_file:
                image_md = ImageMetadata.from_fileobj(md_file)
                md_file.seek(0)
                image_md_sha256sum = hashlib.sha256(md_file.read()).hexdigest()
            if image_md_sha256sum != pack_md.image_md_sha256sum:
                raise RuntimeError('image metadata appears to be corrupt '
                                   '(expected SHA256: {0}, actual: {1})',
                                   pack_md.image_md_sha256sum,
                                   image_md_sha256sum)
            if self.args['profile'] not in image_md.profiles:
                raise ValueError('no such profile: "{0}" (choose from {1})'
                                 .format(self.args['profile'],
                                 ', '.join(image_md.profiles.keys())))
            member = pack.getmember(IMAGE_ARCNAME)
            with contextlib.closing(pack.extractfile(member)) as image:
                # image --> xz_proc -|> digest
                pipe_r, pipe_w = open_pipe_fileobjs()
                if os.fork() == 0:
                    pipe_r.close()
                    xz_proc = subprocess.Popen(
                        ('xz', '-d'), stdin=subprocess.PIPE,
                        stdout=pipe_w, close_fds=True)
                    pipe_w.close()
                    shutil.copyfileobj(image, xz_proc.stdin)
                    xz_proc.stdin.close()
                    xz_proc.wait()
                    os._exit(os.EX_OK)
                pipe_w.close()
                # We could technically hand xz_proc.stdout directly
                # to the installation process and calculate checksums
                # on fly, but that would mean we error out only after
                # everything finishes and force people to clean up after.
                # We thus do this in two steps instead.
                digest = hashlib.sha256()
                bytes_written = 0
                pbar = self.get_progressbar(label='Decompressing',
                                            maxval=pack_md.image_size)
                pbar.start()
                while True:
                    chunk = pipe_r.read(euca2ools.BUFSIZE)
                    if not chunk:
                        break
                    digest.update(chunk)
                    decompressed_image.write(chunk)
                    bytes_written += len(chunk)
                    pbar.update(bytes_written)
                pipe_r.close()
                pbar.finish()
        if digest.hexdigest() != pack_md.image_sha256sum:
            raise RuntimeError('image appears to be corrupt '
                                '(expected SHA256: {0}, actual: {1})',
                                pack_md.image_sha256sum,
                                digest.hexdigest())
        decompressed_image.seek(0)
        image_id = image_md.install_profile(
            self.args['profile'], services, decompressed_image,
            pack_md.image_size, self.args)
        decompressed_image.close()
        return image_id

    def print_result(self, image_id):
        print self.tabify(('IMAGE', image_id))
