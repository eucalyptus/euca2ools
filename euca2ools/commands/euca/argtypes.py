# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Eucalyptus Systems, Inc.
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

import argparse
from requestbuilder import EMPTY

def block_device_mapping(map_as_str):
    '''
    Parse a block device mapping from an image registration command line.
    '''
    try:
        (device, mapping) = map_as_str.split('=')
    except ValueError:
        raise argparse.ArgumentTypeError(
                'block device mapping "{0}" must have form '
                'DEVICE=[SNAP-ID]:[SIZE]:[true|false]'.format(map_as_str))
    map_dict = {}
    if mapping.lower() == 'none':
        map_dict['Ebs'] = {'NoDevice': EMPTY}
    elif mapping.startswith('ephemeral'):
        map_dict['VirtualName'] = mapping
    elif (mapping.startswith('snap-') or mapping.startswith('vol-') or
          mapping.startswith(':')):
        map_bits = mapping.split(':')
        if len(map_bits) == 1:
            map_bits.append(None)
        if len(map_bits) == 2:
            map_bits.append(None)
        if len(map_bits) != 3:
            raise argparse.ArgumentTypeError(
                    'EBS block device mapping "{0}" must have form '
                    'DEVICE=[SNAP-ID]:[SIZE]:[true|false]'.format(map_as_str))

        map_dict['Ebs'] = {}
        if map_bits[0]:
            map_dict['Ebs']['SnapshotId'] = map_bits[0]
        if map_bits[1]:
            try:
                map_dict['Ebs']['VolumeSize'] = int(map_bits[1])
            except ValueError:
                raise argparse.ArgumentTypeError(
                        'second element of EBS block device mapping "{0}" '
                        'must be an integer'.format(map_as_str))
        if map_bits[2]:
            if map_bits[2].lower() not in ('true', 'false'):
                raise argparse.ArgumentTypeError(
                        'third element of EBS block device mapping "{0}" must '
                        'be "true" or "false"'.format(map_as_str))
            map_dict['Ebs']['DeleteOnTermination'] = map_bits[2].lower()
    else:
        raise argparse.ArgumentTypeError(
                'unrecognized block device mapping "{0}"'.format(map_as_str))
    return map_dict

def binary_tag_def(tag_str):
    '''
    Parse a tag definition from the command line.  Return a dict that depends
    on the format of the string given:

     - 'key=value': {'Key': key, 'Value': value}
     - 'key=':      {'Key': key, 'Value': EMPTY}
     - 'key':       {'Key': key, 'Value': EMPTY}
    '''
    if '=' in tag_str:
        (key, val) = tag_str.split('=', 1)
        return {'Key': key,     'Value': val or EMPTY}
    else:
        return {'Key': tag_str, 'Value': EMPTY}
