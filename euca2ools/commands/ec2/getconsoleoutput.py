# Copyright 2009-2014 Eucalyptus Systems, Inc.
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

import base64
from euca2ools.commands.ec2 import EC2Request
from requestbuilder import Arg
import sys


CHAR_ESCAPES = {
    u'\x00': u'^@', u'\x0c': u'^L', u'\x17': u'^W',
    u'\x01': u'^A', u'\x0e': u'^N', u'\x18': u'^X',
    u'\x02': u'^B', u'\x0f': u'^O', u'\x19': u'^Y',
    u'\x03': u'^C', u'\x10': u'^P', u'\x1a': u'^Z',
    u'\x04': u'^D', u'\x11': u'^Q', u'\x1b': u'^[',
    u'\x05': u'^E', u'\x12': u'^R', u'\x1c': u'^\\',
    u'\x06': u'^F', u'\x13': u'^S', u'\x1d': u'^]',
    u'\x07': u'^G', u'\x14': u'^T', u'\x1e': u'^^',
    u'\x08': u'^H', u'\x15': u'^U', u'\x1f': u'^_',
    u'\x0b': u'^K', u'\x16': u'^V', u'\x7f': u'^?',
}


class GetConsoleOutput(EC2Request):
    DESCRIPTION = 'Retrieve console output for the specified instance'
    ARGS = [Arg('InstanceId', metavar='INSTANCE', help='''ID of the instance to
                obtain console output from (required)'''),
            Arg('-r', '--raw-console-output', action='store_true',
                route_to=None,
                help='display raw output without escaping control characters')]

    def print_result(self, result):
        print result.get('instanceId', '')
        print result.get('timestamp', '')
        output = base64.b64decode(result.get('output') or '')
        output = output.decode(sys.stdout.encoding or 'utf-8', 'replace')
        output = output.replace(u'\ufffd', u'?')
        if not self.args['raw_console_output']:
            # Escape control characters
            for char, escape in CHAR_ESCAPES.iteritems():
                output = output.replace(char, escape)
        print output
