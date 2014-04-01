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

from euca2ools.commands.argtypes import ternary_tag_def
from euca2ools.commands.ec2 import EucalyptusRequest
from requestbuilder import Arg


class DeleteTags(EucalyptusRequest):
    DESCRIPTION = 'Delete tags from one or more resources'
    ARGS = [Arg('ResourceId', metavar='RESOURCE', nargs='+', help='''ID(s) of
                the resource(s) to un-tag (at least 1 required)'''),
            Arg('--tag', dest='Tag', metavar='KEY[=[VALUE]]',
                type=ternary_tag_def, action='append', required=True,
                help='''key and optional value of the tag to delete, separated
                by an "=" character.  If you specify a value then the tag is
                deleted only if its value matches the one you specified.  If
                you specify the empty string as the value (e.g. "--tag foo=")
                then the tag is deleted only if its value is the empty
                string.  If you do not specify a value (e.g. "--tag foo") then
                the tag is deleted regardless of its value. (at least 1
                required)''')]
