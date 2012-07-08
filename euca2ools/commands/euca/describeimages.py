# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2012, Eucalyptus Systems, Inc.
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

from requestbuilder import Arg, Filter, GenericTagFilter
from . import EucalyptusRequest

class DescribeImages(EucalyptusRequest):
    Description = '''\
        Show information about images

        By default, only images the caller owns and images for which the caller
        has explicit launch permissions are shown.'''

    APIVersion = '2010-08-31'
    Args = [Arg('ImageId', metavar='IMAGE', nargs='*',
                help='limit results to one or more images'),
            Arg('-a', '--all', action='store_true', route_to=None,
                help='describe all images'),
            Arg('-o', '--owner', dest='Owner', metavar='ACCOUNT',
                action='append',
                help='describe images owned by the specified owner'),
            Arg('-x', '--executable-by', dest='ExecutableBy',
                metavar='ACCOUNT', action='append',
                help='''describe images for which the specified entity has
                        explicit launch permissions''')]
    Filters = [Filter('architecture', choices=('i386', 'x86_64'),
                      help='image architecture'),
               Filter('block-device-mapping.delete-on-termination',
                      help='''whether a volume is deleted upon instance
                              termination'''),
               Filter('block-device-mapping.device-name',
                      help='device name for a volume mapped to the image'),
               Filter('block-device-mapping.snapshot-id',
                      help='snapshot ID for a volume mapped to the image'),
               Filter('block-device-mapping.volume-size',
                      help='volume size for a volume mapped to the image'),
               Filter('description', help='image description'),
               Filter('image-id'),
               Filter('image-type', choices=('machine', 'kernel', 'ramdisk'),
                      help='image type ("machine", "kernel", or "ramdisk")'),
               Filter('is-public', help='whether the image is public'),
               Filter('kernel-id'),
               Filter('manifest-location'),
               Filter('name'),
               Filter('owner-alias', help="image owner's account alias"),
               Filter('owner-id', help="image owner's account ID"),
               Filter('platform', help='"windows" for Windows images'),
               Filter('product-code',
                      help='product code associated with the image'),
               Filter('product-code.type', choices=('devpay', 'marketplace'),
                      help='type of product code associated with the image'),
               Filter('ramdisk-id'),
               Filter('root-device-name'),
               Filter('root-device-type', choices=('ebs', 'instance-store'),
                      help='root device type ("ebs" or "instance-store")'),
               Filter('state', choices=('available', 'pending', 'failed'),
                      help='''image state ("available", "pending", or
                              "failed")'''),
               Filter('state-reason-code',
                      help='reason code for the most recent state change'),
               Filter('state-reason-message',
                      help='message for the most recent state change'),
               Filter('tag-key', help='key of a tag assigned to the image'),
               Filter('tag-value',
                      help='value of a tag assigned to the image'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('virtualization-type', choices=('paravirtual', 'hvm'),
                      help='virtualization type ("paravirtual" or "hvm")'),
               Filter('hypervisor', choices=('ovm', 'xen'),
                      help='image\'s hypervisor type ("ovm" or "xen")')]
    ListDelims = ['imagesSet', 'blockDeviceMapping', 'tagSet']

    def main(self):
        if not any(self.args.get(item) for item in ('all', 'ImageId',
                                                    'ExecutableBy', 'Owner')):
            # Default to owned images and images with explicit launch perms
            self.params = {'Owner': 'self'}
            owned = self.send()
            self.params = {'ExecutableBy': 'self'}
            executable = self.send()
            self.params = None
            owned['imagesSet'] = (owned.get(     'imagesSet', []) +
                                  executable.get('imagesSet', []))
            return owned
        if self.args['all']:
            if self.args.get('ImageId'):
                self._cli_parser.error('argument -a/--all: not allowed with '
                                       'a list of images')
            if self.args.get('ExecutableBy'):
                self._cli_parser.error('argument -a/--all: not allowed with '
                                       'argument -x/--executable-by')
            if self.args.get('Owner'):
                self._cli_parser.error('argument -a/--all: not allowed with '
                                       'argument -o/--owner')
        return self.send()

    def print_result(self, result):
        for image in result.get('imagesSet', []):
            self.print_image(image)

    def print_image(self, image):
        print self.tabify(('IMAGE', image.get('imageId'),
                image.get('imageLocation'),
                image.get('imageOwnerAlias') or image.get('imageOwnerId'),
                image.get('imageState'),
                ('public' if image.get('isPublic') == 'true' else 'private'),
                image.get('architecture'), image.get('imageType'),
                image.get('kernelId'), image.get('ramdiskId'),
                image.get('platform'), image.get('rootDeviceType'),
                image.get('virtualizationType'), image.get('hypervisor')))
        for mapping in image.get('blockDeviceMapping', []):
            self.print_blockdevice_mapping(mapping)
        for tag in image.get('tagSet', []):
            self.print_resource_tag(tag, image.get('imageId'))

    def print_blockdevice_mapping(self, mapping):
        print self.tabify(('BLOCKDEVICEMAPPING', mapping.get('deviceName'),
                           mapping.get('ebs', {}).get('snapshotId'),
                           mapping.get('ebs', {}).get('volumeSize'),
                           mapping.get('ebs', {}).get('deleteOnTermination')))
