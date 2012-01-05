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
import euca2ools.utils


class UpdateUser(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """UpdateUser"""
    Params = [Param(
        name='UserName',
        short_name='u',
        long_name='user-name',
        ptype='string',
        optional=False,
        doc=""" Name of the User to update.  If you're changing the name of the User, this is the original User name. """
            ,
        ), Param(
        name='NewPath',
        short_name='p',
        long_name='new-path',
        ptype='string',
        optional=True,
        doc=""" New path for the User. Include this parameter only if you're changing the User's path. """ ,
        ), Param(
        name='NewUserName',
        short_name='n',
        long_name='new-user-name',
        ptype='string',
        optional=True,
        doc=""" New name for the User. Include this parameter only if you're changing the User's name. """ ,
        ), Param(
        name='Enabled',
        short_name=None,
        long_name='enabled',
        ptype='string',
        optional=True,
        doc=""" [Eucalyptus extension] 'true' if to set user to be enabled. Otherwise 'false'. """ ,
        ), Param(
        name='RegStatus',
        short_name=None,
        long_name='reg-status',
        ptype='string',
        optional=True,
        doc=""" [Eucalyptus extension] New registration status for user. Pick one from REGISTERED, APPROVED or CONFIRMED (use any case combination as you want). Only CONFIRMED user is valid to access the system. """ ,
        ), Param(
        name='PasswordExpiration',
        short_name=None,
        long_name='pwd-expires',
        ptype='string',
        optional=True,
        doc=""" [Eucalyptus extension] New password expiration date. Use ISO8601 format. """ ,
        ), Param(
        name='DelegateAccount',
        short_name=None,
        long_name='delegate',
        ptype='string',
        optional=True,
        doc=""" [Eucalyptus extension] Process this command as if the administrator of the specified account had run it. This option is only usable by cloud administrators. """,
        )]

    def cli_formatter(self, data):
        pass
    
    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        euca2ools.utils.print_version_if_necessary()
        self.do_cli()
