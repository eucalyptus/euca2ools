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

from requestbuilder import Arg, MutuallyExclusiveArgList
from . import EucalyptusRequest

class DescribeImageAttribute(EucalyptusRequest):
    Description = 'Show information about an attribute of an image'
    Args = [Arg('ImageId', metavar='IMAGE', help='image to describe'),
            MutuallyExclusiveArgList(True,
                Arg('-l', '--launch-permission', dest='Attribute',
                    action='store_const', const='launchPermission',
                    help='display launch permissions'),
                Arg('-p', '--product-codes', dest='Attribute',
                    action='store_const', const='productCodes',
                    help='list associated product codes'),
                Arg('-B', '--block-device-mapping', dest='Attribute',
                    action='store_const', const='blockDeviceMapping',
                    help='describe block device mappings'),
                Arg('--kernel', dest='Attribute', action='store_const',
                    const='kernel', help='show associated kernel image ID'),
                Arg('--ramdisk', dest='Attribute', action='store_const',
                    const='ramdisk', help='show associated ramdisk image ID'),
                Arg('--description', dest='Attribute', action='store_const',
                    const='description', help="show the image's description"))]
    ListMarkers = ['blockDeviceMapping', 'launchPermission', 'productCodes']
    ItemMarkers = ['item']

    def print_result(self, result):
        image_id = result.get('imageId')
        for perm in result.get('launchPermission', []):
            for (entity_type, entity_name) in perm.items():
                print self.tabify(('launchPermission', image_id, entity_type,
                                   entity_name))
        for code in result.get('productCodes', []):
            if 'type' in code:
                code_str = '[{0}: {1}]'.format(code['type'],
                                               code.get('productCode'))
            else:
                code_str = code.get('productCode')
            print self.tabify(('productCodes', image_id, 'productCode',
                               code_str))
        for blockdev in result.get('blockDeviceMapping', []):
            blockdev_src = (blockdev.get('virtualName') or
                            blockdev.get('ebs', {}).get('snapshotId'))
            blockdev_str = '{0}: {1}'.format(blockdev.get('deviceName'),
                                             blockdev_src)

            ## TODO:  figure out how to print mappings that create new volumes
            print self.tabify(('blockDeviceMapping', image_id,
                               'blockDeviceMap', blockdev_str))
        if result.get('kernel'):
            print self.tabify(('kernel', image_id, None,
                               result['kernel'].get('value')))
        if result.get('ramdisk'):
            print self.tabify(('ramdisk', image_id, None,
                               result['ramdisk'].get('value')))
        if result.get('description'):
            print self.tabify(('description', image_id, None,
                               result['description'].get('value')))
