# Copyright 2014 Eucalyptus Systems, Inc.
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

from __future__ import division

import argparse
import datetime
import math
import uuid

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin

from euca2ools.commands.argtypes import filesize
from euca2ools.commands.ec2 import EC2Request
from euca2ools.commands.ec2.mixins import S3AccessMixin
from euca2ools.commands.ec2.resumeimport import ResumeImport
from euca2ools.commands.s3.getobject import GetObject
import euca2ools.util


class ImportInstance(EC2Request, S3AccessMixin, FileTransferProgressBarMixin):
    DESCRIPTION = 'Import an instance into the cloud'
    ARGS = [Arg('source', metavar='FILE', route_to=None,
                help='file containing the disk image to import (required)'),
            Arg('-t', '--instance-type', metavar='INSTANCETYPE', required=True,
                dest='LaunchSpecification.InstanceType',
                help='the type of instance to import to (required)'),
            Arg('-f', '--format', dest='DiskImage.1.Image.Format',
                metavar='FORMAT', required=True, help='''the image's format
                ("vmdk", "raw", or "vhd") (required)'''),
            Arg('-a', '--architecture', metavar='ARCH', required=True,
                dest='LaunchSpecification.Architecture',
                help="the instance's processor architecture (required)"),
            Arg('-p', '--platform', dest='Platform', required=True,
                choices=('Windows', 'Linux'),
                help="the instance's operating system (required)"),
            MutuallyExclusiveArgList(
                Arg('-b', '--bucket', route_to=None,
                    help='the bucket to upload the volume to'),
                Arg('--manifest-url', metavar='URL',
                    dest='DiskImage.1.Image.ImportManifestUrl',
                    help='''a pre-signed URL that points to the import
                    manifest to use'''))
            .required(),
            Arg('--prefix', route_to=None, help='''a prefix to add to the
                names of the volume parts as they are uploaded'''),
            Arg('-x', '--expires', metavar='DAYS', type=int, default=30,
                route_to=None, help='''how long the import manifest should
                remain valid, in days (default: 30 days)'''),
            Arg('--no-upload', action='store_true', route_to=None,
                help='''start the import process, but do not actually upload
                the volume (see euca-resume-import)'''),
            Arg('-d', '--description', dest='Description',
                help='a description for the import task (not the volume)'),
            Arg('-g', '--group', metavar='GROUP',
                dest='LaunchSpecification.GroupName.1',
                help='name of the security group to create the instance in'),
            Arg('-z', '--availability-zone', metavar='ZONE',
                dest='LaunchSpecification.Placement.AvailabilityZone',
                help='the zone in which to create the instance'),
            Arg('-s', '--volume-size', metavar='GiB', type=int,
                dest='DiskImage.1.Volume.Size',
                help='size of the volume to import to, in GiB'),
            Arg('--image-size', dest='DiskImage.1.Image.Bytes',
                metavar='BYTES', type=filesize,
                help='size of the image (required for non-raw files'),
            MutuallyExclusiveArgList(
                Arg('--user-data', metavar='DATA',
                    dest='LaunchSpecification.UserData',
                    help='user data to supply to the instance'),
                Arg('--user-data-file', metavar='FILE', type=open,
                    dest='LaunchSpecification.UserData', help='''file
                    containing user data to supply to the instance''')),
            Arg('--subnet', metavar='SUBNET',
                dest='LaunchSpecification.SubnetId', help='''[VPC only] subnet
                to create the instance's network interface in'''),
            Arg('--private-ip-address', metavar='ADDRESS',
                dest='LaunchSpecification.PrivateIpAddress',
                help='''[VPC only] assign a specific primary private IP address
                to the instance's interface'''),
            Arg('--monitor', action='store_true',
                dest='LaunchSpecification.Monitoring.Enabled',
                help='enable detailed monitoring for the instance'),
            Arg('--instance-initiated-shutdown-behavior',
                dest='LaunchSpecification.InstanceInitiatedShutdownBehavior',
                choices=('stop', 'terminate'), help='''whether to "stop"
                (default) or terminate the instance when it shuts down'''),
            Arg('--key', dest='LaunchSpecification.KeyName',
                help='''[Eucalyptus only] name of the key pair to use when
                running the instance'''),
            # This is not yet implemented
            Arg('--ignore-region-affinity', action='store_true', route_to=None,
                help=argparse.SUPPRESS),
            # This does no validation, but it does prevent taking action
            Arg('--dry-run', action='store_true', route_to=None,
                help=argparse.SUPPRESS),
            # This is not yet implemented
            Arg('--dont-verify-format', action='store_true', route_to=None,
                help=argparse.SUPPRESS)]

    def configure(self):
        EC2Request.configure(self)
        self.configure_s3_access()

        if (self.params['DiskImage.1.Image.Format'].upper() in
                ('VMDK', 'VHD', 'RAW')):
            self.params['DiskImage.1.Image.Format'] = \
                self.params['DiskImage.1.Image.Format'].upper()
        if not self.params.get('DiskImage.1.Image.Bytes'):
            if self.params['DiskImage.1.Image.Format'] == 'RAW':
                image_size = euca2ools.util.get_filesize(self.args['source'])
                self.params['DiskImage.1.Image.Bytes'] = image_size
            else:
                raise ArgumentError(
                    'argument --image-size is required for {0} files'
                    .format(self.params['DiskImage.1.Image.Format']))
        if not self.params.get('DiskImage.1.Volume.Size'):
            vol_size = math.ceil(self.params['DiskImage.1.Image.Bytes'] /
                                 2 ** 30)
            self.params['DiskImage.1.Volume.Size'] = int(vol_size)

        if not self.args.get('expires'):
            self.args['expires'] = 30
        if self.args['expires'] < 1:
            raise ArgumentError(
                'argument -x/--expires: value must be positive')

    def main(self):
        if self.args.get('dry_run'):
            return

        if self.args.get('bucket'):
            self.ensure_bucket_exists(self.args['bucket'])

        if not self.args.get('DiskImage.1.Image.ImportManifestUrl'):
            manifest_key = '{0}/{1}.manifest.xml'.format(uuid.uuid4(),
                                                         self.args['source'])
            if self.args.get('prefix'):
                manifest_key = '/'.join((self.args['prefix'], manifest_key))
            getobj = GetObject.from_other(
                self, service=self.args['s3_service'],
                auth=self.args['s3_auth'],
                source='/'.join((self.args['bucket'], manifest_key)))
            days = self.args.get('expires') or 30
            expiration = datetime.datetime.utcnow() + datetime.timedelta(days)
            get_url = getobj.get_presigned_url(expiration)
            self.log.info('generated manifest GET URL: %s', get_url)
            self.params['DiskImage.1.Image.ImportManifestUrl'] = get_url

        result = self.send()

        # The manifest creation and uploading parts are done by ResumeImport.
        if not self.args.get('no_upload'):
            resume = ResumeImport.from_other(
                self, source=self.args['source'],
                task=result['conversionTask']['conversionTaskId'],
                s3_service=self.args['s3_service'],
                s3_auth=self.args['s3_auth'], expires=self.args['expires'],
                show_progress=self.args.get('show_progress', False))
            resume.main()

        return result

    def print_result(self, result):
        self.print_conversion_task(result['conversionTask'])
