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

class DescribeImageAttribute(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Show image attributes.'
    Options = [Param(name='blockDeviceMapping', metavar='block_device_mapping',
                     short_name='B', long_name='block-device-mapping',
                     optional=True, ptype='boolean',
                     doc='show block device mapping.'),
               Param(name='launchPermission', metavar='launch_permission',
                     short_name='l', long_name='launch-permission',
                     optional=True, ptype='boolean',
                     doc='show launch permissions.'),
               Param(name='productCode', metavar='product_code',
                     short_name='p', long_name='product-code',
                     optional=True, ptype='boolean',
                     doc='show the product codes associated with the image.'),
               Param(name='kernel', long_name='kernel',
                     optional=True, ptype='boolean',
                     doc='show the kernel id associated with the image.'),
               Param(name='ramdisk', long_name='ramdisk',
                     optional=True, ptype='boolean',
                     doc='show the ramdisk id associated with the image.')]
    Args = [Param(name='image_id', ptype='string',
                  doc="""unique identifier for the image that you want
                  to retrieve the attributes for.""",
                  cardinality=1, optional=False)]
    
    def display_image_attribute(self, image_id, image_attribute):
        if image_attribute.name == 'launch_permission':
            if image_attribute.attrs.has_key('groups'):
                for group in image_attribute.attrs['groups']:
                    print 'launchPermission\t%s\tgroup\t%s' \
                        % (image_attribute.image_id, group)
            if image_attribute.attrs.has_key('user_ids'):
                for userid in image_attribute.attrs['user_ids']:
                    print 'launchPermission\t%s\tuserId\t%s' \
                        % (image_attribute.image_id, userid)
        if image_attribute.attrs.has_key('product_codes'):
            for product_code in image_attribute.attrs['product_codes']:
                print 'productCodes\t%s\tproductCode\t%s' \
                    % (image_attribute.image_id, product_code)
        if image_attribute.kernel is not None:
            print 'kernel\t%s\t\t%s' % (image_attribute.image_id,
                                        getattr(image_attribute, 'value', ""))
        if image_attribute.ramdisk is not None:
            print 'ramdisk\t%s\t\t%s' % (image_attribute.image_id,
                                         getattr(image_attribute, 'value', ""))
        if image_attribute.attrs.has_key('block_device_mapping'):
            block_device_mapping = \
                image_attribute.attrs['block_device_mapping']
            for dev_name in block_device_mapping:
                print 'blockDeviceMapping\t%s\tblockDeviceMap\t%s: %s' \
                    % (image_id, dev_name,
                       (block_device_mapping[dev_name].ephemeral_name or
                        block_device_mapping[dev_name].snapshot_id))
 
    def main(self):
        attribute = None
        attr_names = [ opt.name for opt in self.Options ]
        for name in attr_names:
            if not attribute:
                if getattr(self, name):
                    attribute = name
        if attribute:
            conn = self.make_connection_cli()
            return self.make_request_cli(conn, 'get_image_attribute',
                                         image_id=self.image_id,
                                         attribute=attribute)
        else:
            msg = 'image attribute must be specified'
            self.display_error_and_exit(msg)

    def main_cli(self):
        image_attribute = self.main()
        if image_attribute:
            self.display_image_attribute(self.image_id,
                                         image_attribute)

