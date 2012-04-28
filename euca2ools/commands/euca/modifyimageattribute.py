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

class ModifyImageAttribute(EucalyptusRequest):
    Description = 'Modify an attribute of an image'
    Args = [Arg('ImageId', metavar='IMAGE', help='image to modify'),
            MutuallyExclusiveArgList(True,
                Arg('--description', dest='Description.Value', metavar='DESC',
                    help="change the image's description"),
                Arg('-p', '--product-code', dest='ProductCode', metavar='CODE',
                    action='append', help='''product code to add to the given
                    instance-store image'''),
                Arg('-l', '--launch-permission', action='store_true',
                    route_to=None,
                    help='grant/revoke launch permissions with -a/-r')),
            Arg('-a', '--add', metavar='ENTITY', action='append', default=[],
                route_to=None, help='''account to grant launch permission, or
                "all" for all accounts'''),
            Arg('-r', '--remove', metavar='ENTITY', action='append',
                default=[], route_to=None, help='''account to remove launch
                permission from , or "all" for all accounts''')]

    def main(self):
        if self.args.get('launch_permission'):
            lp = {}
            for entity in self.args.get('add', []):
                lp.setdefault('Add', [])
                if entity == 'all':
                    lp['Add'].append({'Group':  entity})
                else:
                    lp['Add'].append({'UserId': entity})
            for entity in self.args.get('remove', []):
                lp.setdefault('Remove', [])
                if entity == 'all':
                    lp['Remove'].append({'Group':  entity})
                else:
                    lp['Remove'].append({'UserId': entity})
            if not lp:
                self._cli_parser.error('at least one entity must be specified '
                                       'with -a/--add or -r/--remove')
            self.params = {'LaunchPermission': lp}
        else:
            if self.args.get('add'):
                self._cli_parser.error('argument -a/--add may only be used '
                                       'with -l/--launch-permission')
            if self.args.get('remove'):
                self._cli_parser.error('argument -r/--remove may only be used '
                                       'with -l/--launch-permission')
        return self.send()

    def print_result(self, result):
        if self.args.get('Description.Value'):
            print self.tabify(('description', self.args['ImageId'],
                               None, self.args['Description.Value']))
        if self.args.get('ProductCode'):
            for code in self.args['ProductCode']:
                print self.tabify(('productcodes', self.args['ImageId'],
                                   'productCode',  code))
        if self.args.get('launch_permission'):
            for add in self.params['LaunchPermission'].get('Add', []):
                for (entity_type, entity_name) in add.items():
                    print self.tabify(('launchPermission',
                                       self.args['ImageId'], 'ADD',
                                       entity_type, entity_name))
            for add in self.params['LaunchPermission'].get('Remove', []):
                for (entity_type, entity_name) in add.items():
                    print self.tabify(('launchPermission',
                                       self.args['ImageId'], 'REMOVE',
                                       entity_type, entity_name))
