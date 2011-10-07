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

import euca2ools.commands.eucacommand
from boto.roboto.param import Param

class DescribeImages(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2010-08-31'
    Description = 'Shows information about machine images.'
    Options = [Param(name='all', short_name='a', long_name='all',
                     optional=True, ptype='boolean', default=False,
                     doc='Show all images that the user has access to.'),
               Param(name='owner', short_name='o', long_name='owner',
                     optional=True, ptype='string', cardinality='*',
                     doc="""Show only images owned by the user.
                            Valid values: account ID|self|amazon"""),
               Param(name='executable_by',
                     short_name='x', long_name='executable-by',
                     optional=True, ptype='string', cardinality='*',
                     doc="""Show only images for which user has
                     explicit launch permissions.
                     Valid values: account ID|self|all""")]
    Args = [Param(name='image', ptype='string',
                  cardinality='+', optional=True)]
    Filters = [Param(name='architecture', ptype='string',
                     doc='Image architecture.  Valid values are i386 | x86_64'),
               Param(name='block-device-mapping.delete-on-termination',
                     ptype='boolean',
                     doc="""Whether the Amazon EBS volume is deleted on
                     instance termination."""),
               Param(name='block-device-mapping.device-name', ptype='string',
                     doc="""Device name (e.g., /dev/sdh) for an Amazon EBS volume
                     mapped to the image."""),
               Param(name='block-device-mapping.snapshot-id', ptype='string',
                     doc="""Snapshot ID for an Amazon EBS volume mapped
                     to the image."""),
               Param(name='block-device-mapping.volume-size', ptype='integer',
                     doc="""Volume size for an Amazon EBS volume mapped
                     to the image."""),
               Param(name='description', ptype='string',
                     doc='Description of the AMI'),
               Param(name='hypervisor', ptype='string',
                     doc="""Hypervisor type of the image.
                     Valid values are ovm | xen."""),
               Param(name='image-id', ptype='string',
                     doc='ID of the imageID'),
               Param(name='image-type', ptype='string',
                     doc="""Type of the image.
                     Valid values are machine | kernel | ramdisk"""),
               Param(name='is-public', ptype='boolean',
                     doc='Whether the image is public.'),
               Param(name='kernel-id', ptype='string',
                     doc='Kernel ID.'),
               Param(name='manifest-location', ptype='string',
                     doc='Location of the image manifest.'),
               Param(name='name', ptype='string',
                     doc='Name of the AMI.'),
               Param(name='owner-alias', ptype='string',
                     doc="""AWS account alias (e.g., amazon or self) or
                     AWS account ID that owns the AMI."""),
               Param(name='owner-id', ptype='string',
                     doc='AWS account ID of the image owner.'),
               Param(name='platform', ptype='string',
                     doc="""Use windows if you have Windows based AMIs;
                     otherwise leave blank."""),
               Param(name='product-code', ptype='string',
                     doc='Product code associated with the AMI.'),
               Param(name='ramdisk-id', ptype='string',
                     doc='The ramdisk ID.'),
               Param(name='root-device-name', ptype='string',
                     doc='Root device name of the AMI (e.g., /dev/sda1).'),
               Param(name='root-device-type', ptype='string',
                     doc="""Root device type the AMI uses.
                     Valid Values: ebs | instance-store."""),
               Param(name='state', ptype='string',
                     doc="""State of the image.
                     Valid values: available | pending | failed."""),
               Param(name='state-reason-code', ptype='string',
                     doc='Reason code for the state change.'),
               Param(name='state-reason-message', ptype='string',
                     doc='Message for the state change.'),
               Param(name='tag-key', ptype='string',
                     doc='Key of a tag assigned to the resource.'),
               Param(name='tag-value', ptype='string',
                     doc='Value of a tag assigned to the resource.'),
               Param(name='tag:key', ptype='string',
                     doc="""Filters the results based on a specific
                     tag/value combination."""),
               Param(name='virtualization-type', ptype='string',
                     doc="""Virtualization type of the image.
                     Valid values: paravirtual | hvm""")]
    
    def display_images(self, images):
        for image in images:
            image_string = '%s\t%s\t%s\t%s' % (image.id, image.location,
                    image.ownerId, image.state)
            if image.is_public:
                image_string += '\tpublic'
            else:
                image_string += '\tprivate'

            image_string += '\t%s' % ','.join(image.product_codes)

            for i in [image.architecture, image.type, image.kernel_id,
                      image.ramdisk_id]:
                image_string += '\t%s' % ((' ' if i == None else i))

            if image.platform:
                image_string += '\t%s' % image.platform
            if image.root_device_type:
                image_string += '\t%s' % image.root_device_type
            print 'IMAGE\t%s' % image_string
            if image.block_device_mapping:
                block_dev_mapping = image.block_device_mapping
                if image.root_device_type == 'ebs':
                    block_dev_string = '%s\t%s\t%s' \
                        % (block_dev_mapping.current_name,
                           block_dev_mapping.current_value.snapshot_id,
                           block_dev_mapping.current_value.size)
                    print 'BLOCKDEVICEMAPPING\t%s' % block_dev_string

    def main(self):
        if self.all and (self.owner or self.executable_by or self.image):
            msg = '-a cannot be combined with owner, launch, or image list'
            self.display_error_and_exit(msg)

        # if you specify "-a" then it means return ALL images
        if self.all:
            self.executable_by = []
            self.owner = []
            
        conn = self.make_connection_cli()
        images = self.make_request_cli(conn, 'get_all_images',
                                       image_ids=self.image,
                                       owners=self.owner,
                                       executable_by=self.executable_by)
        return images

    def main_cli(self):
        images = self.main()
        self.display_images(images)
