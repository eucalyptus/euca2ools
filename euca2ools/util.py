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

import datetime
import getpass
import os.path
import stat
import struct
import sys
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
    """
    Like tempfile.mkdtemp, but using /var/tmp as a last resort instead of /tmp.

    This is meant for utilities that create large files, as /tmp is often a
    ramdisk.
    """

    if dir is None:
        dir = (os.getenv('TMPDIR') or os.getenv('TEMP') or os.getenv('TMP') or
               '/var/tmp')
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
# pylint: enable=W0622


def prompt_for_password():
    pass1 = getpass.getpass(prompt='New password: ')
    pass2 = getpass.getpass(prompt='Retype new password: ')
    if pass1 == pass2:
        return pass1
    else:
        print >> sys.stderr, 'error: passwords do not match'
        return prompt_for_password()


def strip_response_metadata(response_dict):
    useful_keys = [key for key in response_dict if key != 'ResponseMetadata']
    if len(useful_keys) == 1:
        return response_dict[useful_keys[0]] or {}
    else:
        return response_dict


def substitute_euca_region(obj):
    if os.getenv('EUCA_REGION') and not os.getenv(obj.REGION_ENVVAR):
        msg = ('EUCA_REGION environment variable is deprecated; use {0} '
               'instead').format(obj.REGION_ENVVAR)
        obj.log.warn(msg)
        print >> sys.stderr, msg
        os.environ[obj.REGION_ENVVAR] = os.getenv('EUCA_REGION')


def magic(config, msg, suffix=None):
    if not sys.stdout.isatty() or not sys.stderr.isatty():
        return ''
    try:
        if config.convert_to_bool(config.get_global_option('magic'),
                                  default=False):
            return '\033[95m{0}\033[0m{1}'.format(msg, suffix or '')
        return ''
    except ValueError:
        return ''


def build_iam_policy(effect, resources, actions):
    policy = {'Statement': []}
    for resource in resources or []:
        sid = datetime.datetime.utcnow().strftime('Stmt%Y%m%d%H%M%S%f')
        statement = {'Sid': sid, 'Effect': effect, 'Action': actions,
                     'Resource': resource}
        policy['Statement'].append(statement)
    return policy


def get_filesize(filename):
    mode = os.stat(filename).st_mode
    if stat.S_ISBLK(mode):
        # os.path.getsize doesn't work on block devices, but we can use lseek
        # to figure it out
        block_fd = os.open(filename, os.O_RDONLY)
        try:
            return os.lseek(block_fd, 0, os.SEEK_END)
        finally:
            os.close(block_fd)
    elif any((stat.S_ISCHR(mode), stat.S_ISFIFO(mode), stat.S_ISSOCK(mode),
              stat.S_ISDIR(mode))):
        raise TypeError("'{0}' does not have a usable file size"
                        .format(filename))
    return os.path.getsize(filename)


def get_vmdk_image_size(filename):
    if get_filesize(filename) < 1024:
        raise ValueError('File {0} is to small to be a valid Stream'
                         ' Optimized VMDK'.format(filename))
    # see https://www.vmware.com/support/developer/vddk/vmdk_50_technote.pdf
    # for header/footer format
    with open(filename, 'rb') as disk:
        data = struct.unpack('<iiiqqqqiqqq?bbbbh433c', disk.read(512))
        if data[9] & 0xffffffffffffffff == 0:
            # move to 1024 bytes from the end and read footer
            disk.seek(-1024, 2)
            data = struct.unpack('<iiiqqqqiqqq?bbbbh433c', disk.read(512))

    # validate
    if 1447904331 != data[0]:
        raise ValueError('File {0} is not a Stream Optimized VMDK'
                         .format(filename))
    if data[2] & 0x10000 == 0:
        raise ValueError('File {0} does not contain compressed parts'
                         .format(filename))
    if data[2] & 0x20000 == 0:
        raise ValueError('File {0} does not have all data present'
                         .format(filename))
    if data[11]:
        raise ValueError('File {0} marked with unclean shutdown'
                         .format(filename))
    if data[16] != 1:
        raise ValueError('File {0} uses unsupported compression algorithm'
                         .format(filename))

    return 512 * data[3]


def check_dict_whitelist(dict_, err_context, whitelist=None):
    if not isinstance(dict_, dict):
        raise ValueError('{0} must be a dict'.format(err_context))
    if whitelist:
        differences = set(dict_.keys()) - set(whitelist)
        if differences:
            raise ValueError('unrecognized {0} argument(s): {1}'
                             .format(err_context, ', '.join(differences)))


def transform_dict(dict_, transformation_dict):
    transformed = {}
    for key, val in dict_.iteritems():
        if key in transformation_dict:
            transformed[transformation_dict[key]] = val
        else:
            transformed[key] = val
    return transformed
