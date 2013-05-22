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

import os
import tempfile


def build_progressbar_label_template(fnames):
    if len(fnames) == 0:
        return None
    elif len(fnames) == 1:
        return '{fname}'
    else:
        max_fname_len = max(len(os.path.basename(fname)) for fname in fnames)
        fmt_template = '{{fname:<{maxlen}}} ({{index:>{lenlen}}}/{total})'
        return fmt_template.format(maxlen=max_fname_len,
                                   lenlen=len(str(len(fnames))),
                                   total=len(fnames))


# pylint: disable=W0622
def mkdtemp_for_large_files(suffix='', prefix='tmp', dir=None):
    '''
    Like tempfile.mkdtemp, but using /var/tmp as a last resort instead of /tmp.

    This is meant for utilities that create large files, as /tmp is often a
    ramdisk.
    '''

    if dir is None:
        dir = (os.getenv('TMPDIR') or os.getenv('TEMP') or os.getenv('TMP') or
               '/var/tmp')
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
# pylint: enable=W0622


def sanitize_path(path):
    """Make a fully expanded and absolute path for us to work with.
    Returns a santized path string.
    :param path: The path string to sanitize.
    """
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))
