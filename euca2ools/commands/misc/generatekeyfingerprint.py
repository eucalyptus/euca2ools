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

import hashlib
import subprocess

from requestbuilder import Arg
from requestbuilder.command import BaseCommand

from euca2ools.commands import Euca2ools


class GenerateKeyFingerprint(BaseCommand):
    DESCRIPTION = ('Show the fingerprint of a private key as it would appear '
                   'in the output of euca-describe-keypairs.\n\nNote that this '
                   "will differ from the key's SSH key fingerprint.")
    SUITE = Euca2ools
    ARGS = [Arg('privkey_filename', metavar='FILE',
                help='file containing the private key (required)')]

    def main(self):
        pkcs8 = subprocess.Popen(
            ('openssl', 'pkcs8', '-in', self.args['privkey_filename'],
             '-nocrypt', '-topk8', '-outform', 'DER'), stdout=subprocess.PIPE)
        privkey = pkcs8.stdout.read()
        fprint = hashlib.sha1(privkey).hexdigest()
        return ':'.join(fprint[i:i+2] for i in range(0, len(fprint), 2))

    def print_result(self, fprint):
        print fprint
