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

from boto.roboto.awsqueryrequest import AWSQueryRequest
from boto.roboto.param import Param
import euca2ools.commands.euare
from euca2ools.commands.euare.listuserpolicies import ListUserPolicies
from euca2ools.commands.euare.deleteuserpolicy import DeleteUserPolicy
from euca2ools.commands.euare.listgroupsforuser import ListGroupsForUser
from euca2ools.commands.euare.removeuserfromgroup import RemoveUserFromGroup
from euca2ools.commands.euare.listsigningcertificates import ListSigningCertificates
from euca2ools.commands.euare.deletesigningcertificate import DeleteSigningCertificate
from euca2ools.commands.euare.listaccesskeys import ListAccessKeys
from euca2ools.commands.euare.deleteaccesskey import DeleteAccessKey

class DeleteUser(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """DeleteUser"""
    Params = [
        Param(name='UserName',
              short_name='u',
              long_name='user-name',
              ptype='string',
              optional=False,
              doc=""" Name of the User to delete. """),
        Param(name='DelegateAccount',
              short_name=None,
              long_name='delegate',
              ptype='string',
              optional=True,
              doc=""" [Eucalyptus extension] Use the parameter only as the system admin to act as the account admin of the specified account without changing to account admin's role. """),
        Param(name='recursive',
              short_name='r',
              long_name='recursive',
              ptype='boolean',
              optional=True,
              request_param=False,
              doc=""" Deletes the Group, removes all Users from the Group and deletes all Policies associated with the Group."""),
        Param(name='IsRecursive',
              short_name='R',
              long_name='recursive-euca',
              ptype='boolean',
              optional=True,
              doc=""" Deletes the User from associated groups and deletes the User's credentials and policies along with the User. """),
        Param(name='pretend',
              short_name='p',
              long_name='pretend',
              ptype='boolean',
              optional=True,
              doc="""Returns a list of credentials and policies that would be deleted, as well as the groups the user would be removed from, if the -r or -R option were actually performed.""")
        ]

    Response = {u'type': u'object', u'name': u'DeleteUserResponse',
                u'properties': [{
        u'type': u'object',
        u'optional': False,
        u'name': u'ResponseMetadata',
        u'properties': [{u'type': u'string', u'optional': False, u'name'
                        : u'RequestId'}],
        }]}


    def cli_formatter(self, data):
        if self.pretend:
            print 'accesskeys'
            for ak in data['access_keys']:
                print '\t%s' % ak['AccessKeyId']
            print 'policies'
            for policy in data['policies']:
                print '\t%s' % policy
            print 'certificates'
            for cert in data['certificates']:
                print '\t%s' % cert['CertificateId']
            print 'groups'
            for group in data['groups']:
                print '\t%s' % group['Arn']
        else:
            AWSQueryRequest.cli_formatter(self, data)
            
    def main(self, **args):
        recursive_local = self.cli_options.recursive or \
            args.get('recursive', False)
        recursive_server = self.cli_options.recursive_euca or \
            args.get('recursive_euca', False)
        self.pretend = self.cli_options.pretend or args.get('pretend', False)
        user_name = self.cli_options.user_name or args.get('user_name', None)
        if recursive_local or (recursive_server and self.pretend):
            obj = ListUserPolicies()
            d = obj.main(user_name=user_name)
            data = {'policies' : d.PolicyNames}
            obj = ListGroupsForUser()
            d = obj.main(user_name=user_name)
            data['groups'] = d.Groups
            obj = ListSigningCertificates()
            d = obj.main(user_name=user_name)
            data['certificates'] = d.Certificates
            obj = ListAccessKeys()
            d = obj.main(user_name=user_name)
            data['access_keys'] = d.AccessKeyMetadata
            if self.pretend:
                return data
            else:
                obj = DeleteAccessKey()
                for ak in data['access_keys']:
                    obj.main(user_name=user_name, user_key_id=ak['AccessKeyId'])
                obj = DeleteUserPolicy()
                for policy in data['policies']:
                    obj.main(user_name=user_name, policy_name=policy)
                obj = DeleteSigningCertificate()
                for cert in data['certificates']:
                    obj.main(user_name=user_name, certificate_id=cert['CertificateId'])
                obj = RemoveUserFromGroup()
                for group in data['groups']:
                    obj.main(group_name=group['GroupName'], user_name=user_name)
        if not self.pretend:
            return self.send(**args)
        
    def main_cli(self):
        self.do_cli()
