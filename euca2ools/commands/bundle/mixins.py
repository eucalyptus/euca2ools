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
import base64
import os.path
import random
import sys

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError

import euca2ools.bundle.manifest
import euca2ools.bundle.util
from euca2ools.commands.argtypes import (b64encoded_file_contents,
                                         delimited_list, filesize,
                                         manifest_block_device_mappings)
from euca2ools.commands.walrus.checkbucket import CheckBucket
from euca2ools.commands.walrus.createbucket import CreateBucket
from euca2ools.commands.walrus.postobject import PostObject
from euca2ools.commands.walrus.putobject import PutObject
from euca2ools.exceptions import AWSError


class BundleCreatingMixin(object):
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

            # Noop, for compatibility
            Arg('--batch', action='store_true', help=argparse.SUPPRESS)]

    ### CONFIG METHODS ###

    def configure_bundle_creds(self):
        # User's X.509 certificate (user-level in config)
        if not self.args.get('cert'):
            config_cert = self.config.get_user_option('certificate')
            if 'EC2_CERT' in os.environ:
                self.args['cert'] = os.getenv('EC2_CERT')
            elif 'EUCA_CERT' in os.environ:  # used by the NC
                self.args['cert'] = os.getenv('EUCA_CERT')
            elif config_cert:
                self.args['cert'] = config_cert
        if self.args.get('cert'):
            self.args['cert'] = os.path.expanduser(os.path.expandvars(
                self.args['cert']))
            _assert_is_file(self.args['cert'], 'user certificate')

        # User's private key (user-level in config)
        if not self.args.get('privatekey'):
            config_privatekey = self.config.get_user_option('private-key')
            if 'EC2_PRIVATE_KEY' in os.environ:
                self.args['privatekey'] = os.getenv('EC2_PRIVATE_KEY')
            if 'EUCA_PRIVATE_KEY' in os.environ:  # used by the NC
                self.args['privatekey'] = os.getenv('EUCA_PRIVATE_KEY')
            elif config_privatekey:
                self.args['privatekey'] = config_privatekey
        if self.args.get('privatekey'):
            self.args['privatekey'] = os.path.expanduser(os.path.expandvars(
                self.args['privatekey']))
            _assert_is_file(self.args['privatekey'], 'private key')

        # Cloud's X.509 cert (region-level in config)
        if not self.args.get('ec2cert'):
            config_privatekey = self.config.get_region_option('certificate')
            if 'EUCALYPTUS_CERT' in os.environ:
                # This has no EC2 equivalent since they just bundle their cert.
                self.args['ec2cert'] = os.getenv('EUCALYPTUS_CERT')
            elif config_privatekey:
                self.args['ec2cert'] = config_privatekey
        if self.args.get('ec2cert'):
            self.args['ec2cert'] = os.path.expanduser(os.path.expandvars(
                self.args['ec2cert']))
            _assert_is_file(self.args['ec2cert'], 'cloud certificate')

        # User's account ID (user-level)
        if not self.args.get('user'):
            config_account_id = self.config.get_user_option('account-id')
            if 'EC2_USER_ID' in os.environ:
                self.args['user'] = os.getenv('EC2_USER_ID')
            elif config_account_id:
                self.args['user'] = config_account_id

        # Now validate everything
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

    def configure_bundle_output(self):
        if (self.args.get('destination') and
                os.path.exists(self.args['destination']) and not
                os.path.isdir(self.args['destination'])):
            raise ArgumentError("argument -d/--destination: '{0}' is not a "
                                "directory".format(self.args['destination']))
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

    def configure_bundle_properties(self):
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

    def generate_encryption_keys(self):
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

    ### MANIFEST GENERATION METHODS ###

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
        manifest.bundled_image_size = sum(part.size for part in partinfo)
        manifest.enc_key = self.args['enc_key']
        manifest.enc_iv = self.args['enc_iv']
        manifest.enc_algorithm = 'AES-128-CBC'  # shouldn't be hardcoded here
        manifest.image_parts = partinfo
        return manifest

    def dump_manifest_to_file(self, manifest, filename, pretty_print=False):
        with open(filename, 'w') as manifest_file:
            manifest_file.write(self.dump_manifest_to_str(
                manifest, pretty_print=pretty_print))

    def dump_manifest_to_str(self, manifest, pretty_print=False):
        return manifest.dump_to_str(self.args['privatekey'], self.args['cert'],
                                    self.args['ec2cert'],
                                    pretty_print=pretty_print)


class BundleUploadingMixin(object):
    ARGS = [Arg('-b', '--bucket', metavar='BUCKET[/PREFIX]', required=True,
                help='bucket to upload the bundle to (required)'),
            Arg('--acl', default='aws-exec-read',
                choices=('public-read', 'aws-exec-read', 'ec2-bundle-read'),
                help='''canned ACL policy to apply to the bundle (default:
                aws-exec-read)'''),
            MutuallyExclusiveArgList(
                Arg('--upload-policy', dest='upload_policy', metavar='POLICY',
                    type=base64.b64encode,
                    help='upload policy to use for authorization'),
                Arg('--upload-policy-file', dest='upload_policy',
                    metavar='FILE', type=b64encoded_file_contents,
                    help=('file containing an upload policy to use for '
                    'authorization'))),
            Arg('--upload-policy-signature', metavar='SIGNATURE',
                help=('signature for the upload policy (required when an '
                'upload policy is used)')),
            Arg('--location', help='''location constraint of the destination
                bucket (default: inferred from s3-location-constraint in
                configuration, or otherwise none)'''),
            Arg('--retry', dest='retries', action='store_const', const=5,
                default=0, help='retry failed uploads up to 5 times')]

    def configure_bundle_upload_auth(self):
        if self.args.get('upload_policy'):
            if not self.args.get('key_id'):
                raise ArgumentError('-I/--access-key-id is required when '
                                    'using an upload policy')
            if not self.args.get('upload_policy_signature'):
                raise ArgumentError('--upload-policy-signature is required '
                                    'when using an upload policy')
            self.auth = None

    def get_bundle_key_prefix(self):
        (bucket, _, prefix) = self.args['bucket'].partition('/')
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        return bucket + '/' + prefix

    def ensure_dest_bucket_exists(self):
        bucket = self.args['bucket'].split('/', 1)[0]
        try:
            req = CheckBucket(bucket=bucket, service=self.service,
                              config=self.config)
            req.main()
        except AWSError as err:
            if err.status_code == 404:
                # No such bucket
                self.log.info("creating bucket '%s'", bucket)
                req = CreateBucket(bucket=bucket,
                                   location=self.args.get('location'),
                                   config=self.config, service=self.service)
                req.main()
            else:
                raise
        # At this point we know we can at least see the bucket, but it's still
        # possible that we can't write to it with the desired key names.  So
        # many policies are in play here that it isn't worth trying to be
        # proactive about it.

    def upload_bundle_file(self, source, dest, show_progress=False,
                           **putobj_kwargs):
        if self.args.get('upload_policy'):
            if show_progress:
                # PostObject does not yet support show_progress
                print source, 'uploading...'
            req = PostObject(source=source, dest=dest,
                             acl=self.args.get('acl') or 'aws-exec-read',
                             Policy=self.args['upload_policy'],
                             Signature=self.args['upload_policy_signature'],
                             AWSAccessKeyId=self.args['key_id'],
                             service=self.service, config=self.config,
                             **putobj_kwargs)
        else:
            req = PutObject(source=source, dest=dest,
                            acl=self.args.get('acl') or 'aws-exec-read',
                            retries=self.args.get('retries') or 0,
                            show_progress=show_progress,
                            service=self.service, config=self.config,
                            **putobj_kwargs)
        req.main()

    def upload_bundle_parts(self, partinfo_in_mpconn, key_prefix,
                            partinfo_out_mpconn=None, part_write_sem=None,
                            **putobj_kwargs):
        try:
            while True:
                part = partinfo_in_mpconn.recv()
                dest = key_prefix + os.path.basename(part.filename)
                self.upload_bundle_file(part.filename, dest, **putobj_kwargs)
                if part_write_sem is not None:
                    # Allow something that's waiting for the upload to finish
                    # to continue
                    part_write_sem.release()
                if partinfo_out_mpconn is not None:
                    partinfo_out_mpconn.send(part)
        except EOFError:
            return
        finally:
            partinfo_in_mpconn.close()
            if partinfo_out_mpconn is not None:
                partinfo_out_mpconn.close()


def _assert_is_file(filename, filetype):
    if not os.path.exists(filename):
        raise ArgumentError("{0} file '{1}' does not exist"
                            .format(filetype, filename))
    if not os.path.isfile(filename):
        raise ArgumentError("{0} file '{1}' is not a file"
                            .format(filetype, filename))
