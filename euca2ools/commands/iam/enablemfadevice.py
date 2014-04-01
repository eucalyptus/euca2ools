# Copyright 2009-2013 Eucalyptus Systems, Inc.
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

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT
from requestbuilder import Arg


class EnableMFADevice(IAMRequest):
    DESCRIPTION = 'Enable an MFA device'
    ARGS = [Arg('-u', '--user-name', dest='UserName', metavar='USER',
                required=True,
                help='user to enable the MFA device for (required)'),
            Arg('-s', '--serial-number', dest='SerialNumber', metavar='SERIAL',
                required=True,
                help='serial number of the MFA device to activate (required)'),
            Arg('-c1', dest='AuthenticationCode1', metavar='CODE',
                required=True, help='''an authentication code emitted by the
                                       MFA device (required)'''),
            Arg('-c2', dest='AuthenticationCode2', metavar='CODE',
                required=True, help='''a subsequent authentication code emitted
                                       by the MFA device (required)'''),
            AS_ACCOUNT]
