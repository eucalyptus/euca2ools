# Copyright 2013 Eucalyptus Systems, Inc.
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

from euca2ools.commands.euca import EucalyptusRequest
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError


class ModifySnapshotAttribute(EucalyptusRequest):
    DESCRIPTION = 'Modify an attribute of a snapshot'
    ARGS = [Arg('SnapshotId', metavar='SNAPSHOT',
                help='ID of the snapshot to modify'),
            Arg('-c', '--create-volume-permission', action='store_true',
                required=True, route_to=None,
                help='grant/revoke volume creation permission with -a/-r'),
            Arg('-a', '--add', metavar='ENTITY', action='append', default=[],
                route_to=None,
                help='account to grant permission, or "all" for all accounts'),
            Arg('-r', '--remove', metavar='ENTITY', action='append',
                default=[], route_to=None, help='''account to remove permission
                from, or "all" for all accounts''')]

    # noinspection PyExceptionInherit
    def preprocess(self):
        if self.args.get('create_volume_permission'):
            cvperm = {}
            for entity in self.args.get('add', []):
                cvperm.setdefault('Add', [])
                if entity == 'all':
                    cvperm['Add'].append({'Group':  entity})
                else:
                    cvperm['Add'].append({'UserId': entity})
            for entity in self.args.get('remove', []):
                cvperm.setdefault('Remove', [])
                if entity == 'all':
                    cvperm['Remove'].append({'Group':  entity})
                else:
                    cvperm['Remove'].append({'UserId': entity})
            if not cvperm:
                raise ArgumentError('at least one entity must be specified '
                                    'with -a/--add or -r/--remove')
            self.params['CreateVolumePermission'] = cvperm
        else:
            if self.args.get('add'):
                raise ArgumentError('argument -a/--add may only be used '
                                    'with -c/--create-volume-permission')
            if self.args.get('remove'):
                raise ArgumentError('argument -r/--remove may only be used '
                                    'with -c/--create-volume-permission')

    def print_result(self, result):
        if self.args.get('create_volume_permission'):
            for add in self.params['CreateVolumePermission'].get('Add', []):
                for (entity_type, entity_name) in add.items():
                    print self.tabify(('createVolumePermission',
                                       self.args['SnapshotId'], 'ADD',
                                       entity_type, entity_name))
            for add in self.params['CreateVolumePermission'].get('Remove', []):
                for (entity_type, entity_name) in add.items():
                    print self.tabify(('createVolumePermission',
                                       self.args['SnapshotId'], 'REMOVE',
                                       entity_type, entity_name))
