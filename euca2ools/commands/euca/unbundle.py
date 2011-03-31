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

import os
from boto.roboto.param import Param
import euca2ools.commands.eucacommand
import euca2ools.bundler
from euca2ools.exceptions import NotFoundError, CommandFailed

class Unbundle(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Unbundles a previously uploaded bundle.'
    Options = [Param(name='manifest_path',
                     short_name='m', long_name='manifest',
                     optional=False, ptype='file',
                     doc='Path to the manifest file.'),
               Param(name='private_key_path',
                     short_name='k', long_name='privatekey',
                     optional=True, ptype='file',
                     doc='Path to private key used to encrypt bundle.'),
               Param(name='destination_dir',
                     short_name='d', long_name='destination',
                     optional=True, ptype='dir', default='.',
                     doc="""Directory to store the image to.
                     Defaults to the current directory."""),
               Param(name='source_dir',
                     short_name='s', long_name='destination',
                     optional=True, ptype='dir',
                     doc="""Source directory for the bundled image parts.
                     Defaults to manifest directory.""")]

def main():
    if not self.source_dir:
        self.source_dir = self.get_file_path(self.manifest_path)
    if not self.private_key_path:
        self.private_key_path = self.get_environ('EC2_PRIVATE_KEY')
        if not os.path.isfile(self.private_key_path):
            msg = 'Private Key not found: %s' % self.private_key_path
            self.display_error_and_exit(msg)

    bundler = euca2ools.bundler.Bundler(self)
    (parts, encrypted_key, encrypted_iv) = \
        bundler.parse_manifest(self.manifest_path)
    image = bundler.assemble_parts(self.source_dir, self.directory,
                                   self.manifest_path, parts)
    print 'Decrypting image'
    decrypted_image = bundler.decrypt_image(image, encrypted_key,
                                            encrypted_iv, self.private_key_path)
    os.remove(image)
    print 'Uncompressing image'
    try:
        unencrypted_image = bundler.untarzip_image(self.directory,
                                                   decrypted_image)
    except NotFoundError:
        sys.exit(1)
    except CommandFailed:
        sys.exit(1)
    os.remove(decrypted_image)

def main_cli(self):
    self.main()

