# Copyright 2011-2013 Eucalyptus Systems, Inc.
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
import copy
from euca2ools.commands.bundle import add_bundle_creds
from euca2ools.commands.bundle.bundleimage import BundleImage
from euca2ools.commands.bundle.uploadbundle import UploadBundle
from euca2ools.commands.euare import Euare
from euca2ools.commands.euare.listaccountaliases import ListAccountAliases
from euca2ools.commands.euca import Eucalyptus
from euca2ools.commands.euca.registerimage import RegisterImage
from euca2ools.commands.eustore import EuStoreRequest
import euca2ools.commands.eustore.describeimages
from euca2ools.commands.walrus import Walrus
from euca2ools.util import mkdtemp_for_large_files
import hashlib
import os.path
import random
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.auth import QuerySigV2Auth, S3RestAuth
import requestbuilder.commands.http
from requestbuilder.exceptions import ArgumentError, ClientError
from requestbuilder.mixins import FileTransferProgressBarMixin
from requestbuilder.util import set_userregion
import shutil
import sys
import tarfile
import urlparse
import zlib


class InstallImage(EuStoreRequest, FileTransferProgressBarMixin):
    DESCRIPTION = 'Download an image from EuStore and add it to your cloud'
    ARGS = [MutuallyExclusiveArgList(True,
            Arg('-i', '--image-name', metavar='EUIMAGE',
                help='name of the image to download and install'),
            Arg('-t', '--tarball', metavar='FILE',
                help='tarball to install the image from')),
            Arg('-b', '--bucket', required=True,
                help='bucket to store the images in (required)'),
            Arg('-s', '--description', metavar='DESC',
                help='image description (required for -t)'),
            Arg('-a', '--architecture', choices=('i386', 'x86_64', 'armhf'),
                help='image architecture (required for -t)'),
            Arg('-p', '--prefix', help='prefix to use when naming the image'),
            Arg('--hypervisor', choices=('xen', 'kvm', 'universal'),
                help='''hypervisor the kernel image is built for (required for
                images with hypervisor-specific kernels'''),
            Arg('--separate-buckets', action='store_true',
                help='''store kernel, ramdisk, and machine images in separate
                buckets (BUCKET-kernel, BUCKET-ramdisk)'''),
            Arg('--virtualization-type', choices=('paravirtual', 'hvm'),
                help='''Virtualization type to register image with'''),
            Arg('-k', '--kernel-type', dest='kernel_type',
                choices=('xen', 'kvm', 'universal'), help=argparse.SUPPRESS),
            Arg('-d', '--directory', dest='directory', metavar='DIR',
                help='''location to place the image and other artifacts
                (default:  dir named by TMPDIR, TEMP, or TMP environment
                variables, or otherwise /var/tmp)'''),
            Arg('--pad-name', action='store_true', help='''add some random
                characters to the image's name to ensure it is unique'''),
            Arg('--kernel', help='''ID of the kernel image to use instead of
                the one bundled with the image'''),
            Arg('--ramdisk', help='''ID of the ramdisk image to use instead of
                the one bundled with the image'''),
            Arg('-I', '--access-key-id', dest='key_id', metavar='KEY_ID'),
            Arg('-S', '--secret-key', dest='secret_key', metavar='KEY'),
            Arg('-c', '--cert', metavar='FILE',
                help='file containing your signing certificate'),
            Arg('--privatekey', metavar='FILE', help='''file containing the
                private key to sign the bundle's manifest with.  This private
                key will also be required to unbundle the image in the
                future.'''),
            Arg('--ec2cert', metavar='FILE', help='''file containing the
                cloud's X.509 certificate'''),
            Arg('-u', '--user', metavar='ACCOUNT', help='your account ID'),
            Arg('--ec2-url', metavar='URL',
                help='compute service endpoint URL'),
            Arg('--iam-url', metavar='URL',
                help='identity service endpoint URL'),
            Arg('--s3-url', metavar='URL',
                help='storage service endpoint URL'),
            Arg('-y', '--yes', action='store_true', help=argparse.SUPPRESS)]

    # noinspection PyExceptionInherit
    def configure(self):
        EuStoreRequest.configure(self)
        set_userregion(self.config, self.args.get('userregion'))

        if self.args.get('kernel_type'):
            # Use it and complain
            self.args['hypervisor'] = self.args['kernel_type']
            msg = ('argument -k/--kernel-type is deprecated; use --hypervisor '
                   'instead')
            self.log.warn(msg)
            print >> sys.stderr, 'warning:', msg

        # Get bundle creds first
        add_bundle_creds(self.args, self.config)
        if not self.args.get('cert'):
            raise ArgumentError(
                'missing certificate; please supply one with -c')
        self.log.debug('certificate: %s', self.args['cert'])
        if not self.args.get('privatekey'):
            raise ArgumentError(
                'missing private key; please supply one with --privatekey')
        self.log.debug('private key: %s', self.args['privatekey'])
        if not self.args.get('ec2cert'):
            raise ArgumentError(
                'missing cloud certificate; please supply one with --ec2cert')
        self.log.debug('cloud certificate: %s', self.args['ec2cert'])
        if not self.args.get('user'):
            raise ArgumentError(
                'missing account ID; please supply one with --user')
        self.log.debug('account ID: %s', self.args['user'])

        # Set up the web services -- we're going to use them a lot
        query_auth = QuerySigV2Auth(self.config,
                                    key_id=self.args.get('key_id'),
                                    secret_key=self.args.get('secret_key'))
        self.__euare = Euare(self.config, loglevel=self.log.level,
                             auth=copy.copy(query_auth),
                             url=self.args.get('iam_url'))
        self.log.debug('configuring euare service')
        self.__euare.configure()
        self.__eucalyptus = Eucalyptus(self.config, loglevel=self.log.level,
                                       auth=copy.copy(query_auth),
                                       url=self.args.get('ec2_url'))
        self.log.debug('configuring eucalyptus service')
        self.__eucalyptus.configure()
        s3_auth = S3RestAuth(self.config, key_id=self.args.get('key_id'),
                             secret_key=self.args.get('secret_key'))
        self.__walrus = Walrus(self.config, loglevel=self.log.level,
                               auth=s3_auth, url=self.args.get('s3_url'))
        self.__walrus.configure()

        # Check other args next
        if self.args.get('tarball'):
            if not self.args.get('architecture'):
                raise ArgumentError('argument -a/--architecture is required '
                                    'when -t/--tarball is used')
            if not self.args.get('hypervisor'):
                raise ArgumentError('argument --hypervisor is required when '
                                    '-t/--tarball is used')
            self.args['tarball'] = os.path.expanduser(os.path.expandvars(
                self.args['tarball']))
            if not os.path.exists(self.args['tarball']):
                raise ArgumentError("tarball file '{0}' does not exist"
                                    .format(self.args['tarball']))
            if not os.path.isfile(self.args['tarball']):
                raise ArgumentError("tarball file '{0}' is not a file"
                                    .format(self.args['tarball']))
        if self.args.get('kernel') and not self.args.get('ramdisk'):
            raise ArgumentError('argument --kernel: --ramdisk is required')
        if self.args.get('ramdisk') and not self.args.get('kernel'):
            raise ArgumentError('argument --ramdisk: --kernel is required')
        if self.args.get('image') and self.args.get('architecture'):
            self.log.warn("downloaded image's architecture may be overridden")

    def ensure_kernel_reg_privs(self):
        req = ListAccountAliases(service=self.__euare, config=self.config)
        response = req.main()
        for alias in response.get('AccountAliases', []):
            if alias == 'eucalyptus':
                self.log.debug("found account alias '%s'; ok to register "
                               "kernel/ramdisk images", alias)
                return
        raise ClientError("kernel/ramdisk images may only be registered by "
                          "the 'eucalyptus' account")

    def main(self):
        if (self.args.get('kernel') and self.args.get('ramdisk')) and self.args.get('virtualization_type') != "hvm":
            self.ensure_kernel_reg_privs()

        if self.args.get('directory'):
            workdir = self.args['directory']
            should_delete_workdir = False
        else:
            workdir = mkdtemp_for_large_files()
            self.log.debug('created working directory %s', workdir)
            should_delete_workdir = True

        tarball_path = self.get_tarball(workdir=workdir)
        image_ids = self.bundle_and_register_all(workdir, tarball_path)
        if should_delete_workdir:
            shutil.rmtree(workdir)
        return image_ids

    def print_result(self, image_ids):
        print 'Installed new image', image_ids['machine']

    def get_tarball(self, workdir):
        if self.args.get('tarball'):
            self.log.info('using local tarball %s', self.args['tarball'])
            return self.args['tarball']
        else:
            # Download one
            req = euca2ools.commands.eustore.describeimages.DescribeImages(
                service=self.service, config=self.config)
            eustore_images = req.main()
            for image in eustore_images.get('images', []):
                if image.get('name') == self.args['image_name']:
                    break
            else:
                raise KeyError("no such image: '{0}'"
                               .format(self.args['image_name']))
            # pylint: disable=W0631
            self.log.debug('image data: %s', str(image))
            if self.args.get('architecture') is None:
                self.args['architecture'] = image.get('architecture')
            if self.args.get('description') is None:
                self.args['description'] = image.get('description')
            if bool(image.get('single-kernel', False)):
                self.log.debug('image catalog data specify single-kernel; '
                               "setting hypervisor to 'universal'")
                self.args['hypervisor'] = 'universal'
            if self.args.get('virtualization_type') is None:
                self.args['virtualization_type'] = image.get('virtualization_type')
            if not self.args.get('hypervisor'):
                raise RuntimeError("image '{0}' uses hypervisor-specific "
                                   "kernels; please specify a hypervisor with "
                                   "--hypervisor"
                                   .format(self.args['image_name']))
            if self.service.endpoint.endswith('/'):
                endpoint = self.service.endpoint
            else:
                endpoint = self.service.endpoint + '/'
            url = urlparse.urljoin(endpoint, image['url'])
            self.log.info('downloading image from %s', url)
            label = 'Downloading image '.format(os.path.basename(url))
            req = requestbuilder.commands.http.Get(
                label=label, url=url,
                show_progress=self.args.get('show_progress', False),
                dest=workdir, config=self.config)
            tarball_path, tarball_size = req.main()
            self.log.info('downloaded %i bytes to %s', tarball_size,
                          tarball_path)

            expected_crc = image['name']  # Yes, really.
            real_crc = self.calc_file_checksum(tarball_path)
            if real_crc != expected_crc:
                raise RuntimeError('downloaded file is incomplete or corrupt '
                                   '(checksum: {0}, expected: {1})'
                                   .format(real_crc, expected_crc))
            return tarball_path
            # pylint: enable=W0631

    def calc_file_checksum(self, filename):
        filesize = os.path.getsize(filename)
        pbar = self.get_progressbar(label='Verifying image   ',
                                    maxval=filesize)
        digest = hashlib.md5()
        with open(filename) as file_:
            pbar.start()
            while file_.tell() < filesize:
                chunk = file_.read(4096)
                digest.update(chunk)
                pbar.update(file_.tell())
        pbar.finish()
        crc = zlib.crc32(digest.hexdigest()) & 0xffffffff
        return '{0:0>10d}'.format(crc)

    def bundle_and_register_all(self, workdir, tarball_filename):
        if self.args['show_progress']:
            print 'Preparing to extract image...'
        if self.args.get('pad_name', False):
            image_name_pad = '{0:0>8x}-'.format(random.randrange(16**8))
        else:
            image_name_pad = ''
        image_name = 'eustore-{0}{1}'.format(
            image_name_pad,
            os.path.splitext(os.path.basename(tarball_filename))[0]
            .replace('.', '_'))
        tarball = tarfile.open(tarball_filename, 'r:gz')
        try:
            members = tarball.getmembers()
            filenames = tuple(member.name for member in members)
            commonprefix = os.path.commonprefix(filenames)
            kernel_id = self.args.get('kernel')
            ramdisk_id = self.args.get('ramdisk')
            if self.args['hypervisor'] == 'universal' or self.args['virtualization_type'] == 'hvm':
                hv_prefix = commonprefix
            else:
                hv_type_dir = self.args['hypervisor'] + '-kernel'
                hv_prefix = os.path.join(commonprefix, hv_type_dir)
            # Get any kernel and ramdisk images we're missing
            bundled_images = []
            for member in members:
                if member.name.startswith(hv_prefix):
                    if kernel_id is None and 'vmlinu' in member.name:
                        # Note that vmlinux/vmlinuz is not always at the
                        # beginning of the file name
                        bundled_images.append(member.name)
                        kernel_image = self.extract_without_path(
                            tarball, member, workdir, 'Extracting kernel ')
                        manifest_loc = self.bundle_and_upload_image(
                            kernel_image, 'kernel', workdir)
                        req = RegisterImage(
                            config=self.config, service=self.__eucalyptus,
                            ImageLocation=manifest_loc,
                            Name=(image_name + '-kernel'),
                            Description=self.args.get('description'),
                            Architecture=self.args.get('architecture'))
                        response = req.main()
                        kernel_id = response.get('imageId')
                        if self.args['show_progress']:
                            print 'Registered kernel image', kernel_id
                    elif (ramdisk_id is None and
                          any(s in member.name for s in ('initrd', 'initramfs',
                                                         'loader'))):
                        bundled_images.append(member.name)
                        ramdisk_image = self.extract_without_path(
                            tarball, member, workdir, 'Extracting ramdisk')
                        manifest_loc = self.bundle_and_upload_image(
                            ramdisk_image, 'ramdisk', workdir)
                        req = RegisterImage(
                            config=self.config, service=self.__eucalyptus,
                            ImageLocation=manifest_loc,
                            Name=(image_name + '-ramdisk'),
                            Description=self.args.get('description'),
                            Architecture=self.args.get('architecture'))
                        response = req.main()
                        ramdisk_id = response.get('imageId')
                        if self.args['show_progress']:
                            print 'Registered ramdisk image', ramdisk_id
            if kernel_id is None and self.args['virtualization_type'] != 'hvm':
                raise RuntimeError('failed to find a useful kernel image')
            if ramdisk_id is None and self.args['virtualization_type'] != 'hvm':
                raise RuntimeError('failed to find a useful ramdisk image')
            # Now that we have kernel and ramdisk image IDs, deal with the
            # machine image
            machine_id = None
            for member in members:
                if member.name in bundled_images:
                    continue
                if any(s in member.name for s in ('initrd', 'initramfs',
                                                  'loader')):
                    # Make sure we don't accidentally register a ramdisk image.
                    # This can happen when use of --ramdisk prevents us from
                    # pruning it later.
                    continue
                if machine_id is None and (member.name.endswith('.img') or member.name.endswith('.raw')):
                    bundled_images.append(member.name)
                    machine_image = self.extract_without_path(
                        tarball, member, workdir, 'Extracting image  ')
                    manifest_loc = self.bundle_and_upload_image(
                        machine_image, 'machine', workdir, kernel_id=kernel_id,
                        ramdisk_id=ramdisk_id)
                    req = RegisterImage(
                        config=self.config, service=self.__eucalyptus,
                        ImageLocation=manifest_loc, Name=image_name,
                        Description=self.args.get('description'),
                        Architecture=self.args.get('architecture'),
                        VirtualizationType=self.args.get('virtualization_type'))
                    response = req.main()
                    machine_id = response.get('imageId')
                    if self.args['show_progress']:
                        print 'Registered machine image', machine_id
        finally:
            tarball.close()
        if self.args['show_progress']:
            print '-- Done --'
        return {'machine': machine_id, 'kernel': kernel_id,
                'ramdisk': ramdisk_id}

    def extract_without_path(self, tarball, member, destdir, bar_label):
        dest_filename = os.path.join(destdir, os.path.basename(member.name))
        self.log.info('extracting %s from tarball to %s', member.name,
                      dest_filename)
        src = tarball.extractfile(member)
        pbar = self.get_progressbar(label=bar_label, maxval=member.size)
        try:
            with open(dest_filename, 'w') as dest:
                while dest.tell() < member.size:
                    # The first chunk may take a while to read since gzip
                    # doesn't support seeking.
                    chunk = src.read(16384)
                    dest.write(chunk)
                    if pbar.start_time is None:
                        pbar.start()
                    pbar.update(dest.tell())
                pbar.finish()
        finally:
            src.close()
        return dest_filename

    def bundle_and_upload_image(self, image, image_type, workdir,
                                kernel_id=None, ramdisk_id=None):
        unique_bucket = self.args['bucket']
        if image_type == 'machine':
            image_type_args = {'kernel': kernel_id,
                               'ramdisk': ramdisk_id}
            progressbar_label = 'Bundling image    '
        elif image_type == 'kernel':
            image_type_args = {'kernel': 'true'}
            progressbar_label = 'Bundling kernel   '
            if self.args.get('separate_buckets'):
                unique_bucket = ''.join([self.args['bucket'], '-kernel'])
        elif image_type == 'ramdisk':
            image_type_args = {'ramdisk': 'true'}
            progressbar_label = 'Bundling ramdisk  '
            if self.args.get('separate_buckets'):
                unique_bucket = ''.join([self.args['bucket'], '-ramdisk'])
        else:
            raise ValueError("unrecognized image type: '{0}'"
                             .format(image_type))
        cmd = BundleImage(config=self.config, image=image,
                          arch=self.args['architecture'],
                          cert=self.args['cert'],
                          privatekey=self.args['privatekey'],
                          ec2cert=self.args['ec2cert'], user=self.args['user'],
                          destination=workdir, image_type=image_type,
                          show_progress=self.args.get('show_progress', False),
                          progressbar_label=progressbar_label,
                          **image_type_args)
        __, manifest_path = cmd.main()

        if self.args.get('show_progress', False):
            print '-- Uploading {0} image --'.format(image_type)
        cmd = UploadBundle(config=self.config, service=self.__walrus,
                           bucket=unique_bucket, manifest=manifest_path,
                           acl='aws-exec-read',
                           show_progress=self.args.get('show_progress', False))
        manifest_loc = cmd.main()
        return manifest_loc
