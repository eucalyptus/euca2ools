# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
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
#
# Author: Neil Soman neil@eucalyptus.com
#         Mitch Garnaat mgarnaat@eucalyptus.com

import argparse
import os
import sys
import platform
import euca2ools.bundler
import euca2ools.metadata
from euca2ools.commands.bundle.helpers import get_metadata, get_metadata_dict
from euca2ools.commands.bundle.imagecreator import ImageCreator
from euca2ools.exceptions import AWSError
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError
from requestbuilder.command import BaseCommand
from requestbuilder.mixins import FileTransferProgressBarMixin
from requestbuilder.util import set_userregion


IMAGE_MAX_SIZE_IN_MB = euca2ools.bundler.IMAGE_MAX_SIZE / 1024 // 1024


class BundleVol(BundleCommand):
    DESCRIPTION = 'Bundles an image for use with Eucalyptus or Amazon EC2.'
    ARGS = [Arg('-s', '--size', metavar='SIZE',
                type=filesize, default=IMAGE_MAX_SIZE_IN_MB,
                help="""Size of the image in MB (default: {0}; recommended
                maximum: {0})""").format(IMAGE_MAX_SIZE_IN_MB)),
            Arg('-p', '--prefix', default='image', help='''the file name prefix
                to give the bundle's files (defaults to 'image')'''),
            Arg('-a', '--all', dest="bundle_all_dirs", action='store_true',
                help="""Bundle all directories (including
                mounted filesystems."""),
            MutuallyExclusiveArgList(
                Arg('--no-inherit', dest='inherit',
                    action='store_false', help="""Do not add instance metadata to
                    the bundled image."""),
                Arg('--inherit', dest='inherit', action='store_true',
                    help=argparse.SUPPRESS)),
            Arg('-e', '--exclude', type=delimited_list(','),
                help='''Comma-separated list of directories to exclude.'''),
            Arg('--volume', dest='bundle_volume', default='/',
                help='Path to mounted volume to bundle.'),
            Arg('--no-filter', dest='filter', default=True,
                action='store_false', help="""Do not use the default filtered
                files list."""),
            MutuallyExclusiveArgList(
                Arg('--fstab', dest='fstab',
                    help='Path to the fstab to be bundled with image.'),
                Arg('--generate-fstab', dest='generate_fstab',
                    action='store_true',
                    help='Generate fstab to bundle in image.')),
            Arg('--batch',
                help='Run in batch mode.  For compatibility has no effect')]

    def _check_root(self):
        if os.geteuid() != 0:
            print >> sys.stderr, 'Must be superuser to execute this command.'
            sys.exit(1)

    def _inherit_metadata(self):
        try:
            if not self.args.get('ramdisk_id'):
                self.args['ramdisk_id'] = get_metadata('ramdisk-id')
            if not self.args.get('kernel_id'):
                self.args['kernel_id'] = get_metadata('kernel-id')
            if not self.args.get('block_dev_mapping'):
                self.args['block_dev_mapping'] = \
                    get_metadata_dict('block-device-mapping')
            #
            # Product codes and ancestor AMI ids are special cases since they
            # aren't supported by Eucalyptus yet.
            #
            try:
                self.args['productcodes'].extend(get_metadata_list('product-codes'))
            except MetadataReadError:
                print >> sys.stderr, 'Unable to read product codes.'
            try:
                self.args['ancestor_ami_ids'].extend(
                    get_metadata_list('ancestor-ami-ids'))
            except MetadataReadError:
                print >> sys.stderr, 'Unable to read ancestor ids.'
        except MetadataReadError:
            print >> sys.stderr, 'Unable to read instance metadata.'
            print >> sys.stderr, 'Pass the --no-inherit option if you wish to', \
                'exclude instance metadata.'
            sys.exit(1)

    def main(self):
        self._check_root()

        if self.args.get('inherit') is True:
            self._inherit_metadata()
        
        # No need to check existence.
        # Requirement check is in BundleCommand's configure method.
        self.args['user'] = self.args.get('user').replace('-', '')

        image_file = ImageCreator(self.args).run()
        print "Image Created: ", image_file
