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

from requestbuilder import Arg

from euca2ools.commands.euare import EuareRequest, AS_ACCOUNT


class DeleteRole(EuareRequest):
    DESCRIPTION = 'Delete a role'
    ARGS = [Arg('-r', '--role', dest='RoleName', required=True,
                help='name of the role to delete (required)'),
            Arg('-c', '--recursive', action='store_true', route_to=None,
                help='''remove all IAM resources associated with the role
                first'''),
            Arg('-p', '--pretend', action='store_true', route_to=None,
                help='''list the resources that would be deleted instead of
                actually deleting them.  Implies -c.'''),
            AS_ACCOUNT]

    def main(self):
        if self.args.get('recursive') or self.args.get('pretend'):
            # Figure out what we have to delete
            pass  ## TODO
        else:
            # Just in case
            pass  ## TODO:  fill in empty lists for the stuff to delete
        if self.args.get('pretend'):
            return {}  ## TODO:  return a dict with stuff
        else:
            if self.args.get('recursive'):
                pass  ## TODO
        return self.send()

    def print_result(self, result):
        if self.args.get('pretend'):
            print result  ## TODO:  print the stuff in the dict
