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

import argparse
import os.path
import random
import sys
import tarfile

from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin
from requestbuilder.util import set_userregion

import euca2ools
from euca2ools.bundle.pipes.core import (create_bundle_pipeline,
                                         copy_with_progressbar)
from euca2ools.bundle.pipes.fittings import (create_bundle_part_writer,
                                             create_mpconn_aggregator)
## TODO:  euca2oold.bundle.util.open_pipe_fileobjs should probably be moved
import euca2ools.bundle.util
from euca2ools.commands import Euca2ools
from euca2ools.commands.argtypes import (delimited_list, filesize,
                                         manifest_block_device_mappings)
from euca2ools.util import mkdtemp_for_large_files


class BundleImage(BaseCommand, FileTransferProgressBarMixin):
    SUITE = Euca2ools
    DESCRIPTION = ("Begin preparing an image for uploading to the cloud, and "
                   "return the image's parts as they are generated")  ## FIXME
    ARGS = [Arg('-i', '--image', metavar='FILE', required=True,
                help='file containing the image to bundle (required)'),
            Arg('-p', '--prefix', help='''the file name prefix to give the
                bundle's files (required when bundling stdin; otherwise
                defaults to the image's file name)'''),
            Arg('-d', '--destination', metavar='DIR', help='''location to place
                the bundle's files (default:  dir named by TMPDIR, TEMP, or TMP
                environment variables, or otherwise /var/tmp)'''),
            Arg('-r', '--arch', required=True,
                choices=('i386', 'x86_64', 'armhf', 'ppc', 'ppc64'),
                help="the image's architecture (required)"),

            # User- and cloud-specific stuff
            Arg('-k', '--privatekey', metavar='FILE', help='''file containing
                your private key to sign the bundle's manifest with.  This
                private key will also be required to unbundle the image in the
                future.'''),
            Arg('-c', '--cert', metavar='FILE',
                help='file containing your X.509 certificate'),
            Arg('--ec2cert', metavar='FILE', help='''file containing the
                cloud's X.509 certificate'''),
            Arg('-u', '--user', metavar='ACCOUNT', help='your account ID'),
            Arg('--region', dest='userregion', metavar='USER@REGION',
                help='''user and/or region to use for obtaining keys and
                account info'''),
            Arg('--kernel', metavar='IMAGE', help='''ID of the kernel image to
                associate with this machine image'''),
            Arg('--ramdisk', metavar='IMAGE', help='''ID of the ramdisk image
                to associate with this machine image'''),

            # Obscurities
            Arg('-B', '--block-device-mappings',
                metavar='VIRTUAL1=DEVICE1,VIRTUAL2=DEVICE2,...',
                type=manifest_block_device_mappings,
                help='''block device mapping scheme with which to launch
                instances of this machine image'''),
            Arg('--productcodes', metavar='CODE1,CODE2,...',
                type=delimited_list(','), default=[],
                help='comma-separated list of product codes for the image'),
            Arg('--image-type', choices=('machine', 'kernel', 'ramdisk'),
                default='machine', help=argparse.SUPPRESS),

            # Stuff needed to fill out TarInfo when input comes from stdin.
            #
            # We technically could ask for a lot more, but most of it is
            # unnecessary since owners/modes/etc will be ignored at unbundling
            # time anyway.
            #
            # When bundling stdin we interpret --prefix as the image's file
            # name.
            Arg('--image-size', type=filesize, help='''the image's size
                (required when bundling stdin)'''),

            # Overrides for debugging and other entertaining uses
            Arg('--part-size', type=filesize, default=10485760,  # 10M
                help=argparse.SUPPRESS),
            Arg('--enc-key', type=(lambda s: int(s, 16)),
                help=argparse.SUPPRESS),  # a hex string
            Arg('--enc-iv', type=(lambda s: int(s, 16)),
                help=argparse.SUPPRESS),  # a hex string
            Arg('--progressbar_label', help=argparse.SUPPRESS),

            # Noop, for compatibility
            Arg('--batch', action='store_true', help=argparse.SUPPRESS)]


    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)
        set_userregion(self.config, self.args.get('userregion'))
        set_userregion(self.config, os.getenv('EUCA_REGION'))

        # Get creds
        add_bundle_creds(self.args, self.config)
        if not self.args.get('cert'):
            raise ArgumentError(
                'missing certificate; please supply one with -c')
        self.log.debug('certificate: %s', self.args['cert'])
        if not self.args.get('privatekey'):
            raise ArgumentError(
                'missing private key; please supply one with -k')
        self.log.debug('private key: %s', self.args['privatekey'])
        if not self.args.get('ec2cert'):
            raise ArgumentError(
                'missing cloud certificate; please supply one with --ec2cert')
        self.log.debug('cloud certificate: %s', self.args['ec2cert'])
        if not self.args.get('user'):
            raise ArgumentError(
                'missing account ID; please supply one with --user')
        self.log.debug('account ID: %s', self.args['user'])

        if (self.args.get('destination') and
            os.path.exists(self.args['destination']) and not
            os.path.isdir(self.args['destination'])):
            raise ArgumentError("argument -d/--destination: '{0}' is not a "
                                "directory".format(self.args['destination']))

        # kernel/ramdisk image IDs
        if self.args.get('kernel') == 'true':
            self.args['image_type'] = 'kernel'
        if self.args.get('ramdisk') == 'true':
            self.args['image_type'] = 'ramdisk'
        if self.args['image_type'] == 'kernel':
            if self.args.get('kernel') and self.args['kernel'] != 'true':
                raise ArgumentError("argument --kernel: not compatible with "
                                    "image type 'kernel'")
            if self.args.get('ramdisk'):
                raise ArgumentError("argument --ramdisk: not compatible with "
                                    "image type 'kernel'")
            if self.args.get('block_device_mappings'):
                raise ArgumentError("argument -B/--block-device-mappings: not "
                                    "compatible with image type 'kernel'")
        if self.args['image_type'] == 'ramdisk':
            if self.args.get('kernel'):
                raise ArgumentError("argument --kernel: not compatible with "
                                    "image type 'ramdisk'")
            if self.args.get('ramdisk') and self.args['ramdisk'] != 'true':
                raise ArgumentError("argument --ramdisk: not compatible with "
                                    "image type 'ramdisk'")
            if self.args.get('block_device_mappings'):
                raise ArgumentError("argument -B/--block-device-mappings: not "
                                    "compatible with image type 'ramdisk'")

        if self.args['image'] == '-':
            self.args['image'] = sys.stdin
            if not self.args.get('prefix'):
                raise ArgumentError(
                    'argument --prefix is required when bundling stdin')
            if not self.args.get('image_size'):
                raise ArgumentError(
                    'argument --image-size is required when bundling stdin')
        elif isinstance(self.args['image'], basestring):
            if not self.args.get('prefix'):
                self.args['prefix'] = os.path.basename(self.args['image'])
            self.args['image_size'] = os.path.getsize(self.args['image'])
            self.args['image'] = open(self.args['image'])
        else:
            # Assume it is already a file object
            if not self.args.get('prefix'):
                raise ArgumentError('argument --prefix is required when '
                                    'bundling a file object')
            if not self.args.get('image_size'):
                raise ArgumentError('argument --image-size is required when '
                                    'bundling a file object')

        self._generate_encryption_keys()

    def main(self):
        if self.args.get('destination'):
            path_prefix = os.path.join(self.args['destination'],
                                       self.args['prefix'])
            if not os.path.exists(self.args['destination']):
                os.mkdir(self.args['destination'])
        else:
            tempdir = mkdtemp_for_large_files(prefix='bundle-')
            path_prefix = os.path.join(tempdir, self.args['prefix'])
        self.log.debug('bundle path prefix: %s', path_prefix)

        # First create the bundle
        digest, partinfo = self.create_bundle(path_prefix)

        # All done; now build the manifest and write it to disk
        manifest = self.build_manifest(digest, partinfo)
        ec2cert_fingerprint = euca2ools.bundle.util.get_cert_fingerprint(
            self.args['ec2cert'])
        manifest_filename = '{0}.{1}.manifest.xml'.format(
            path_prefix, ec2cert_fingerprint[-8:])
        with open(manifest_filename, 'w') as manifest_file:
            manifest.dump_to_file(manifest_file, self.args['privatekey'],
                                  self.args['cert'], self.args['ec2cert'])

        # Then we just inform the caller of all the files we wrote.
        # Manifests are returned in a tuple for future expansion, where we
        # bundle for more than one region at a time.
        return (part.filename for part in partinfo), (manifest_filename,)

    def print_result(self, result):
        for manifest_filename in result[1]:
            print 'Wrote manifest', manifest_filename

    def create_bundle(self, path_prefix):
        # Fill out all the relevant info needed for a tarball
        tarinfo = tarfile.TarInfo(self.args['prefix'])
        tarinfo.size = self.args['image_size']

        # The pipeline begins with self.args['image'] feeding a bundling pipe
        # segment through a progress meter, which has to happen on the main
        # thread, so we add that to the pipeline last.

        # meter --(bytes)--> bundler
        bundle_in_r, bundle_in_w = euca2ools.bundle.util.open_pipe_fileobjs()
        partwriter_in_r, partwriter_in_w = \
            euca2ools.bundle.util.open_pipe_fileobjs()
        digest_result_mpconn = create_bundle_pipeline(
            bundle_in_r, partwriter_in_w, self.args['enc_key'],
            self.args['enc_iv'], tarinfo)
        bundle_in_r.close()
        partwriter_in_w.close()

        # bundler --(bytes)-> part writer
        bundle_partinfo_mpconn = create_bundle_part_writer(
            partwriter_in_r, path_prefix, self.args['part_size'])
        partwriter_in_r.close()

        # part writer --(part info)-> part info aggregator
        # (needed for building the manifest)
        bundle_partinfo_aggregate_mpconn = create_mpconn_aggregator(
            bundle_partinfo_mpconn)
        bundle_partinfo_mpconn.close()

        # disk --(bytes)-> bundler
        # (synchronous)
        label = self.args.get('progressbar_label') or 'Bundling image'
        pbar = self.get_progressbar(label=label, maxval=self.args['image_size'])
        with self.args['image'] as image:
            read_size = copy_with_progressbar(image, bundle_in_w,
                                              progressbar=pbar)
        bundle_in_w.close()
        if read_size != self.args['image_size']:
            raise RuntimeError('corrupt bundle: input size did not match '
                               'expected image size  (expected size: {0}, '
                               'read: {1})'
                               .format(self.args['image_size'], read_size))

        # All done; now grab info about the bundle we just created
        try:
            digest = digest_result_mpconn.recv()
            partinfo = bundle_partinfo_aggregate_mpconn.recv()
        except EOFError:
            self.log.debug('EOFError from reading bundle info', exc_info=True)
            raise RuntimeError(
                'corrupt bundle: bundle process was interrupted')
        finally:
            digest_result_mpconn.close()
            bundle_partinfo_aggregate_mpconn.close()
        self.log.debug('%i bundle parts written', len(partinfo))
        self.log.debug('bundle digest: %s', digest)
        return digest, partinfo

    def build_manifest(self, digest, partinfo):
        manifest = euca2ools.bundle.manifest.BundleManifest(
            loglevel=self.log.level)
        manifest.image_arch = self.args['arch']
        manifest.kernel_id = self.args.get('kernel')
        manifest.ramdisk_id = self.args.get('ramdisk')
        if self.args.get('block_device_mappings'):
            manifest.block_device_mappings.update(
                self.args['block_device_mappings'])
        if self.args.get('productcodes'):
            manifest.product_codes.extend(self.args['productcodes'])
        manifest.image_name = self.args['prefix']
        manifest.account_id = self.args['user']
        manifest.image_type = self.args['image_type']
        manifest.image_digest = digest
        manifest.image_digest_algorithm = 'SHA1'  # shouldn't be hardcoded here
        manifest.image_size = self.args['image_size']
        manifest.enc_key = self.args['enc_key']
        manifest.enc_iv = self.args['enc_iv']
        manifest.enc_algorithm = 'AES-128-CBC'  # shouldn't be hardcoded here
        manifest.image_parts = partinfo
        return manifest

    def _generate_encryption_keys(self):
        srand = random.SystemRandom()
        if self.args.get('enc_key'):
            self.log.info('using preexisting encryption key')
            enc_key_i = self.args['enc_key']
        else:
            enc_key_i = srand.getrandbits(128)
        if self.args.get('enc_iv'):
            self.log.info('using preexisting encryption IV')
            enc_iv_i = self.args['enc_iv']
        else:
            enc_iv_i = srand.getrandbits(128)
        self.args['enc_key'] = '{0:0>32x}'.format(enc_key_i)
        self.args['enc_iv'] = '{0:0>32x}'.format(enc_iv_i)


## TODO:  move this
# noinspection PyExceptionInherit
def add_bundle_creds(args, config):
    # User's X.509 certificate (user-level in config)
    if not args.get('cert'):
        config_cert = config.get_user_option('certificate')
        if 'EC2_CERT' in os.environ:
            args['cert'] = os.getenv('EC2_CERT')
        elif 'EUCA_CERT' in os.environ:  # used by the NC
            args['cert'] = os.getenv('EUCA_CERT')
        elif config_cert:
            args['cert'] = config_cert
    if args.get('cert'):
        args['cert'] = os.path.expanduser(os.path.expandvars(args['cert']))
        if not os.path.exists(args['cert']):
            raise ArgumentError("certificate file '{0}' does not exist"
                                .format(args['cert']))
        if not os.path.isfile(args['cert']):
            raise ArgumentError("certificate file '{0}' is not a file"
                                .format(args['cert']))

    # User's private key (user-level in config)
    if not args.get('privatekey'):
        config_privatekey = config.get_user_option('private-key')
        if 'EC2_PRIVATE_KEY' in os.environ:
            args['privatekey'] = os.getenv('EC2_PRIVATE_KEY')
        if 'EUCA_PRIVATE_KEY' in os.environ:  # used by the NC
            args['privatekey'] = os.getenv('EUCA_PRIVATE_KEY')
        elif config_privatekey:
            args['privatekey'] = config_privatekey
    if args.get('privatekey'):
        args['privatekey'] = os.path.expanduser(os.path.expandvars(
            args['privatekey']))
        if not os.path.exists(args['privatekey']):
            raise ArgumentError("private key file '{0}' does not exist"
                                .format(args['privatekey']))
        if not os.path.isfile(args['privatekey']):
            raise ArgumentError("private key file '{0}' is not a file"
                                .format(args['privatekey']))

    # Cloud's X.509 cert (region-level in config)
    if not args.get('ec2cert'):
        config_privatekey = config.get_region_option('certificate')
        if 'EUCALYPTUS_CERT' in os.environ:
            # This has no EC2 equivalent since they just bundle their cert.
            args['ec2cert'] = os.getenv('EUCALYPTUS_CERT')
        elif config_privatekey:
            args['ec2cert'] = config_privatekey
    if args.get('ec2cert'):
        args['ec2cert'] = os.path.expanduser(os.path.expandvars(
            args['ec2cert']))
        if not os.path.exists(args['ec2cert']):
            raise ArgumentError("cloud certificate file '{0}' does not exist"
                                .format(args['ec2cert']))
        if not os.path.isfile(args['ec2cert']):
            raise ArgumentError("cloud certificate file '{0}' is not a file"
                                .format(args['ec2cert']))

    # User's account ID (user-level)
    if not args.get('user'):
        config_account_id = config.get_user_option('account-id')
        if 'EC2_USER_ID' in os.environ:
            args['user'] = os.getenv('EC2_USER_ID')
        elif config_account_id:
            args['user'] = config_account_id
