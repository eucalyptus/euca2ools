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
import copy
import os
import sys
from euca2ools.commands.argtypes import delimited_list, filesize
from euca2ools.commands.bundle import BundleCommand
from euca2ools.commands.bundle.bundleimage import BundleImage
from euca2ools.commands.bundle.helpers import (check_metadata, get_metadata,
                                               get_metadata_dict,
                                               get_metadata_list)
from euca2ools.commands.bundle.imagecreator import ImageCreator, IMAGE_MAX_SIZE
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ServerError


IMAGE_MAX_SIZE_IN_MB = IMAGE_MAX_SIZE / 1024 // 1024
#
# We pass our args dict along to BundleImage so we need to remove all the
# args that it doesn't understand.
#
BUNDLE_IMAGE_ARG_FILTER = ('generate_fstab', 'fstab', 'bundle_all_dirs',
                           'filter', 'inherit', 'size', 'volume',
                           'exclude', 'include', 'ancestor_image_ids')


class BundleVol(BundleCommand):
    DESCRIPTION = 'Bundles an image for use with Eucalyptus or Amazon EC2.'
    ARGS = [Arg('-s', '--size', metavar='MB',
                type=filesize, default=IMAGE_MAX_SIZE_IN_MB,
                help='''Size of the image in MB (default: {0}; recommended
                maximum: {0}).'''.format(IMAGE_MAX_SIZE_IN_MB)),
            Arg('-p', '--prefix', metavar='PREFIX', default='image',
                help='''the file name prefix to give the bundle's files
                (defaults to 'image').'''),
            Arg('-a', '--all', dest="bundle_all_dirs", action='store_true',
                help='''Bundle all directories (including mounted
                filesystems).'''),
            MutuallyExclusiveArgList(
                Arg('--no-inherit', dest='inherit', default=False,
                    action='store_false', help='''Do not add instance metadata to
                    the bundled image (use the --inherit option to explicitly
                    inherit instance metadata).'''),
                Arg('--inherit', dest='inherit', default=True,
                    action='store_true', help=argparse.SUPPRESS)),
            Arg('-i', '--include', metavar='FILE1,FILE2,...',
                type=delimited_list(','), help='''Comma-separated list of
                absolute file paths to include.'''),
            Arg('-e', '--exclude', metavar='DIR1,DIR2,...',
                type=delimited_list(','), help='''Comma-separated list of
                directories to exclude.'''),
            Arg('--volume', metavar='PATH', default='/', help='''Path to
                mounted volume to bundle (defaults to '/').'''),
            Arg('--no-filter', dest='filter', default=True,
                action='store_false', help='''Do not use the default filtered
                files list.'''),
            MutuallyExclusiveArgList(
                Arg('--fstab', metavar='PATH', help='''Path to the fstab to be
                    bundled with image.'''),
                Arg('--generate-fstab', default=False, action='store_true',
                    help='Generate fstab to bundle in image.')),
            Arg('--batch',
                help='Run in batch mode.  For compatibility has no effect')]

    def __init__(self, **kwargs):
        #
        # Do root check before anything else happens
        #
        if os.geteuid() != 0:
            raise Exception("must be root user to run euca-bundle-vol.")
        BaseCommand.__init__(self, **kwargs)

    def _inherit_metadata(self):
        """Read instance metadata which we will propagate to the BundleImage
        command. These values are used for generating a manifest once we have
        a bundled image.
        """
        try:
            check_metadata()

            if not self.args.get('ramdisk'):
                self.args['ramdisk'] = get_metadata('ramdisk-id')
                self.log.debug("inheriting ramdisk: {0}"
                               .format(self.args.get('ramdisk')))
            if not self.args.get('kernel'):
                self.args['kernel'] = get_metadata('kernel-id')
                self.log.debug("inheriting kernel: {0}"
                               .format(self.args.get('kernel')))
            if not self.args.get('block_device_mappings'):
                self.args['block_device_mappings'] = \
                    get_metadata_dict('block-device-mapping')
                self.log.debug("inheriting block device mappings: {0}"
                               .format(self.args.get('block_device_mappings')))
            #
            # Product codes and ancestor ids are special cases since they
            # aren't always there.
            #
            try:
                self.args['productcodes'].extend(
                    get_metadata_list('product-codes'))
            except ServerError:
                msg = 'unable to read product codes from metadata.'
                print sys.stderr, msg
                self.log.warn(msg)
            try:
                if not self.args.get('ancestor_image_ids'):
                    self.args['ancestor_image_ids'] = []
                self.args['ancestor_image_ids'].extend(
                    get_metadata_list('ancestor-ami-ids'))
            except ServerError:
                msg = 'unable to read ancestor ids.'
                print sys.stderr, msg
                self.log.warn(msg)
        except ServerError:
            print >> sys.stderr, 'Unable to read instance metadata.'
            print >> sys.stderr, 'Pass the --no-inherit option if you wish to', \
                'exclude instance metadata.'
            raise
            
    def _filter_args_for_bundle_image(self):
        """Make a complete copy of args to pass along to BundleImage. We first
        need to remove any arguments that BundleImage would not know about.
        """
        args = copy.deepcopy(self.args)
        for arg in BUNDLE_IMAGE_ARG_FILTER:
            try:
                del args[arg]
            except KeyError:
                pass
        return args

    def configure(self):
        BundleCommand.configure(self)
        self.args['user'] = self.args.get('user').replace('-', '')

    def main(self):
        if self.args.get('inherit') is True:
            self._inherit_metadata()
        
        image_file = ImageCreator(log=self.log, **self.args).run()
        image_args = self._filter_args_for_bundle_image()
        image_args.update(image=image_file, image_type='machine')
        self.log.info("bundling image: {0}".format(image_file))
        return BundleImage(**image_args).main()

    def print_result(self, result):
        for part_filename in result[0]:
            print 'Wrote', part_filename
        print 'Wrote manifest', result[1]
