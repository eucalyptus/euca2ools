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

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.ec2 import EC2Request


class DescribeSnapshotAttribute(EC2Request):
    DESCRIPTION = 'Show information about an attribute of a snapshot'
    ARGS = [Arg('SnapshotId', metavar='SNAPSHOT', help='snapshot to describe'),
            MutuallyExclusiveArgList(
                Arg('-c', '--create-volume-permission', dest='Attribute',
                    action='store_const', const='createVolumePermission',
                    help='display who can create volumes from the snapshot'),
                Arg('-p', '--product-codes', dest='Attribute',
                    action='store_const', const='productCodes',
                    help='list associated product codes'))
            .required()]
    LIST_TAGS = ['createVolumePermission', 'productCodes']

    def print_result(self, result):
        snapshot_id = result.get('snapshotId')
        for perm in result.get('createVolumePermission', []):
            for (entity_type, entity_name) in perm.items():
                print self.tabify(('createVolumePermission', snapshot_id,
                                   entity_type, entity_name))
        for code in result.get('productCodes', []):
            if 'type' in code:
                code_str = '[{0}: {1}]'.format(code['type'],
                                               code.get('productCode'))
            else:
                code_str = code.get('productCode')
            print self.tabify(('productCodes', snapshot_id, 'productCode',
                               code_str))
