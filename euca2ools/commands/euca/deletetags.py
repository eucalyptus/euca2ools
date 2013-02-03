# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2013, Eucalyptus Systems, Inc.
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

from requestbuilder import Arg
from . import EucalyptusRequest
from .argtypes import ternary_tag_def

class DeleteTags(EucalyptusRequest):
    API_VERSION = '2010-08-31'
    DESCRIPTION = 'Delete tags from one or more resources'
    ARGS = [Arg('ResourceId', metavar='RESOURCE', nargs='+',
                help='IDs of the resource(s) to un-tag'),
            Arg('--tag', dest='Tag', metavar='KEY[=[VALUE]]',
                type=ternary_tag_def, action='append', required=True,
                help='''key and optional value of the tag to delete, separated
                        by an "=" character.  If no value is given, but a "="
                        character is, then the tag is deleted if its value is
                        not an empty string.  If neither a value nor a "="
                        character is given then the tag with that key is
                        deleted regardless of its value.''')]

    def print_result(self, result):
        pass
