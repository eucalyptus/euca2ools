# Software License Agreement (BSD License)
#
# Copyright (c) 20092011, Eucalyptus Systems, Inc.
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

class ModifyImageAttribute(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Show image attributes.'
    Options = [Param(name='launchPermission', metavar='launch_permission',
                     short_name='l', long_name='launch-permission',
                     optional=True, ptype='boolean',
                     doc='show launch permissions.'),
               Param(name='productCode', metavar='product_code',
                     short_name='p', long_name='product-code',
                     optional=True, ptype='string', cardinality='*',
                     doc='show the product codes associated with the image.'),
               Param(name='add', short_name='a', long_name='add',
                     optional=True, ptype='string', cardinality='*',
                     doc='Entity (typically, user id) to add.'),
               Param(name='remove', short_name='r', long_name='remove',
                     optional=True, ptype='string', cardinality='*',
                     doc='Entity (typically, user id) to remove.')]
    Args = [Param(name='image_id', ptype='string',
                  doc="""unique identifier for the image that you want
                  to modify the attributes of.""",
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
                       block_device_mapping[dev_name])

    def main(self):
        users = []
        groups = []
        image_attribute = None
        operation_type = 'add'
        if self.productCode:
            image_attribute = 'productCodes'
        if not image_attribute and self.launchPermission:
            image_attribute = 'launchPermission'
        if self.add and self.remove:
            msg = 'You cannot add and remove in the same call'
            self.display_error_and_exit(msg)
        if self.add:
            operation_type = 'add'
        if self.remove:
            operation_type = 'remove'
        users = self.add + self.remove
        if 'all' in users:
            users.remove('all')
            groups.append('all')
        if image_attribute:
            conn = self.make_connection_cli()
            return self.make_request_cli(conn, 'modify_image_attribute',
                                         image_id=self.image_id,
                                         attribute=image_attribute,
                                         operation=operation_type,
                                         user_ids=users,
                                         groups=groups,
                                         product_codes=self.productCode)
        else:
            msg = 'No attributes were specified'
            self.display_error_and_exit(msg)

    def main_cli(self):
        self.main()
        print 'IMAGE\t%s' % self.image_id

