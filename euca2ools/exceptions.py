# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Eucalyptus Systems, Inc.
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


class EucaError(Exception):

    def __init__(self):
        self._message = ''

    @property
    def message(self):
        return self._message

    @property
    def args(self):
        return (self._message,)

class ValidationError(Exception):

    @property
    def message(self):
        return self._message

class AddressValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid address'

class InstanceValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid instance id'

class VolumeValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid volume id'

class SizeValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid size'

class SnapshotValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid snapshot id'

class ProtocolValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid protocol'

class FileValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid file'

class DirValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid directory'

class BundleValidationError(ValidationError):

    def __init__(self):
        self._message = 'Invalid bundle id'

class CopyError(EucaError):

    def __init__(self):
        self._message = 'Unable to copy'

class NotFoundError(EucaError):

    def __init__(self):
        self._message = 'Unable to find'

class UnsupportedException(EucaError):

    def __init__(self, msg=None):
        if msg:
            self._message = 'Not supported: {0}'.format(msg)
        else:
            self._message = 'Not supported'

class CommandFailed(EucaError):

    def __init__(self, cmd=None, err=None):
        self._message = 'Command failed'
        self.err = err
        if cmd:
            self._message += ': {0}'.format(cmd)
        if err:
            self._message += '\n{0}'.format(err)

class ConnectionFailed(EucaError):

    def __init__(self):
        self._message = 'Connection failed'

class ParseError(EucaError):

    def __init__(self, msg):
        self._message = msg

######## NEW CODE STARTS HERE ########

import io
import requestbuilder.exceptions
from requestbuilder.xmlparse import parse_aws_xml
import six

class AWSError(requestbuilder.exceptions.ServerError):
    def __init__(self, response, *args):
        requestbuilder.exceptions.ServerError.__init__(self, response, *args)
        self.code = None  # API error code
        self.message = None  # Error message
        self.elements = {}  # Elements in the error response's body

        if self.body:
            try:
                parsed = parse_aws_xml(io.StringIO(six.text_type(self.body)))
                parsed = parsed[parsed.keys()[0]]  # Strip off the root element
                if 'Errors' in parsed:
                    # This could probably be improved, but meh.  Patches are
                    # welcome.  :)
                    parsed = parsed['Errors']
                if 'Error' in parsed:
                    parsed = parsed['Error']
                if parsed.get('Code'):
                    self.code = parsed['Code']
                    self.args += (parsed['Code'],)
                self.message = parsed.get('Message')
                self.elements = parsed
            except ValueError:
                # Dump the unparseable message body so we don't include
                # unusable garbage in the exception.  Since Eucalyptus
                # frequently returns plain text and/or broken XML, store it
                # in case we need it later.
                self.message = self.body
            self.args += (self.message,)

    def format_for_cli(self):
        return 'error ({0}): {1}'.format(self.code or self.status_code,
                                         self.message or self.reason)
