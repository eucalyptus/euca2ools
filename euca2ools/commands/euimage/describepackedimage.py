# (C) Copyright 2014 Eucalyptus Systems, Inc.
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
from requestbuilder.command import BaseCommand
from requestbuilder.mixins import TabifyingMixin

import euca2ools.commands
from euca2ools.commands.euimage.pack import ImagePack


class DescribePackedImage(BaseCommand, TabifyingMixin):
    SUITE = euca2ools.commands.Euca2ools
    DESCRIPTION = '***TECH PREVIEW***\n\nShow info about an image pack'
    ARGS = [Arg('pack_filename', metavar='FILE',
                help='the image pack to show info for (required)')]

    def main(self):
        return ImagePack.open(self.args['pack_filename'])

    def print_result(self, pack):
        print self.tabify(('Name:', pack.image_md.name))
        print self.tabify(('Architecture:', pack.image_md.arch))
        if pack.image_md.epoch:
            print self.tabify(('Epoch:', pack.image_md.epoch))
        print self.tabify(('Version:', pack.image_md.version))
        print self.tabify(('Release:', pack.image_md.release))
        for profile_name in sorted(pack.image_md.profiles):
            print self.tabify(('Profile:', profile_name))
        print 'Description:'
        print pack.image_md.description
