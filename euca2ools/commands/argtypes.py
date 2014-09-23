# Copyright 2012-2014 Eucalyptus Systems, Inc.
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

import argparse
import base64
import sys

from requestbuilder import EMPTY


def manifest_block_device_mappings(mappings_as_str):
    mappings = {}
    mapping_strs = mappings_as_str.split(',')
    for mapping_str in mapping_strs:
        if mapping_str.strip():
            bits = mapping_str.strip().split('=')
            if len(bits) == 2:
                mappings[bits[0].strip()] = bits[1].strip()
            else:
                raise argparse.ArgumentTypeError(
                    "invalid device mapping '{0}' (must have format "
                    "'VIRTUAL=DEVICE')".format(mapping_str))
    return mappings


def ec2_block_device_mapping(map_as_str):
    """
    Parse a block device mapping from an image registration command line.
    """
    try:
        (device, mapping) = map_as_str.split('=')
    except ValueError:
        raise argparse.ArgumentTypeError(
            'block device mapping "{0}" must have form DEVICE=MAPPED'
            .format(map_as_str))
    map_dict = {'DeviceName': device}
    if mapping.lower() == 'none':
        map_dict['NoDevice'] = 'true'
    elif mapping.startswith('ephemeral'):
        map_dict['VirtualName'] = mapping
    elif (mapping.startswith('snap-') or mapping.startswith('vol-') or
          mapping.startswith(':')):
        map_bits = mapping.split(':')
        while len(map_bits) < 5:
            map_bits.append(None)
        if len(map_bits) != 5:
            raise argparse.ArgumentTypeError(
                'EBS block device mapping "{0}" must have form '
                'DEVICE=[SNAP-ID]:[GiB]:[true|false]:[standard|TYPE[:IOPS]]'
                .format(map_as_str))

        map_dict['Ebs'] = {}
        if map_bits[0]:
            map_dict['Ebs']['SnapshotId'] = map_bits[0]
        if map_bits[1]:
            try:
                map_dict['Ebs']['VolumeSize'] = int(map_bits[1])
            except ValueError:
                raise argparse.ArgumentTypeError(
                    'second element of EBS block device mapping "{0}" must be '
                    'an integer'.format(map_as_str))
        if map_bits[2]:
            if map_bits[2].lower() not in ('true', 'false'):
                raise argparse.ArgumentTypeError(
                    'third element of EBS block device mapping "{0}" must be '
                    '"true" or "false"'.format(map_as_str))
            map_dict['Ebs']['DeleteOnTermination'] = map_bits[2].lower()
        if map_bits[3]:
            map_dict['Ebs']['VolumeType'] = map_bits[3]
        if map_bits[4]:
            if map_bits[3] == 'standard':
                raise argparse.ArgumentTypeError(
                    'fifth element of EBS block device mapping "{0}" is not '
                    'allowed with volume type "standard"'.format(map_as_str))
            map_dict['Ebs']['Iops'] = map_bits[4]
        if not map_dict['Ebs']:
            raise argparse.ArgumentTypeError(
                'EBS block device mapping "{0}" must specify at least one '
                'element.  Use "{1}=none" to suppress an existing mapping.'
                .format(map_as_str, device))
    elif not mapping:
        raise argparse.ArgumentTypeError(
            'invalid block device mapping "{0}".  Use "{1}=none" to suppress '
            'an existing mapping.'.format(map_as_str, device))
    else:
        raise argparse.ArgumentTypeError(
            'invalid block device mapping "{0}"'.format(map_as_str))
    return map_dict


def flexible_bool(bool_str):
    if bool_str.strip().lower() in ('0', 'f', 'false', 'n', 'no'):
        return False
    if bool_str.strip().lower() in ('1', 't', 'true', 'y', 'yes'):
        return True
    raise argparse.ArgumentTypeError("'{0}' must be 'true' or 'false'"
                                     .format(bool_str))


def filesize(size):
    suffixes = 'kmgt'
    s_size = size.lower().rstrip('b')
    if len(s_size) > 0 and s_size[-1] in suffixes:
        multiplier = 1024 ** (suffixes.find(s_size[-1]) + 1)
        s_size = s_size[:-1]
    else:
        multiplier = 1
    return multiplier * int(s_size)


def vpc_interface(iface_as_str):
    """
    Nine-part VPC network interface definition:
    [INTERFACE]:INDEX:[SUBNET]:[DESCRIPTION]:[PRIV_IP]:[GROUP1,GROUP2,...]:
    [true|false]:[SEC_IP_COUNT|:SEC_IP1,SEC_IP2,...]
    """

    if len(iface_as_str) == 0:
        raise argparse.ArgumentTypeError(
            'network interface definitions must be non-empty'.format(
                iface_as_str))

    bits = iface_as_str.split(':')
    iface = {}

    if len(bits) < 2:
        raise argparse.ArgumentTypeError(
            'network interface definition "{0}" must consist of at least 2 '
            'elements ({1} provided)'.format(iface_as_str, len(bits)))
    elif len(bits) > 9:
        raise argparse.ArgumentTypeError(
            'network interface definition "{0}" must consist of at most 9 '
            'elements ({1} provided)'.format(iface_as_str, len(bits)))
    while len(bits) < 9:
        bits.append(None)

    if bits[0]:
        # Preexisting NetworkInterfaceId
        if bits[0].startswith('eni-') and len(bits[0]) == 12:
            iface['NetworkInterfaceId'] = bits[0]
        else:
            raise argparse.ArgumentTypeError(
                'first element of network interface definition "{0}" must be '
                'a network interface ID'.format(iface_as_str))
    if bits[1]:
        # DeviceIndex
        try:
            iface['DeviceIndex'] = int(bits[1])
        except ValueError:
            raise argparse.ArgumentTypeError(
                'second element of network interface definition "{0}" must be '
                'an integer'.format(iface_as_str))
    else:
        raise argparse.ArgumentTypeError(
            'second element of network interface definition "{0}" must be '
            'non-empty'.format(iface_as_str))
    if bits[2]:
        # SubnetId
        if bits[2].startswith('subnet-'):
            iface['SubnetId'] = bits[2]
        else:
            raise argparse.ArgumentTypeError(
                'third element of network interface definition "{0}" must be '
                'a subnet ID'.format(iface_as_str))
    if bits[3]:
        # Description
        iface['Description'] = bits[3]
    if bits[4]:
        # PrivateIpAddresses.n.PrivateIpAddress
        # PrivateIpAddresses.n.Primary
        iface.setdefault('PrivateIpAddresses', [])
        iface['PrivateIpAddresses'].append({'PrivateIpAddress': bits[4],
                                            'Primary': 'true'})
    if bits[5]:
        # SecurityGroupId.n
        groups = [bit for bit in bits[5].split(',') if bit]
        if not all(group.startswith('sg-') for group in groups):
            raise argparse.ArgumentTypeError(
                'sixth element of network interface definition "{0}" must '
                'refer to security groups by IDs, not names'
                .format(iface_as_str))
        iface['SecurityGroupId'] = groups
    if bits[6]:
        # DeleteOnTermination
        if bits[6] in ('true', 'false'):
            iface['DeleteOnTermination'] = bits[6]
        else:
            raise argparse.ArgumentTypeError(
                'seventh element of network interface definition "{0}" '
                'must be "true" or "false"'.format(iface_as_str))
    if bits[7]:
        # SecondaryPrivateIpAddressCount
        if bits[8]:
            raise argparse.ArgumentTypeError(
                'eighth and ninth elements of network interface definition '
                '"{0}" must not both be non-empty'.format(iface_as_str))
        try:
            iface['SecondaryPrivateIpAddressCount'] = int(bits[7])
        except ValueError:
            raise argparse.ArgumentTypeError(
                'eighth element of network interface definition "{0}" must be '
                'an integer'.format(iface_as_str))
    if bits[8]:
        # PrivateIpAddresses.n.PrivateIpAddress
        sec_ips = [{'PrivateIpAddress': addr} for addr in
                   bits[8].split(',') if addr]
        iface.setdefault('PrivateIpAddresses', [])
        iface['PrivateIpAddresses'].extend(sec_ips)
    return iface


def file_contents(filename):
    if filename == '-':
        return sys.stdin.read()
    else:
        with open(filename) as arg_file:
            return arg_file.read()


def b64encoded_file_contents(filename):
    if filename == '-':
        return base64.b64encode(sys.stdin.read())
    else:
        with open(filename) as arg_file:
            return base64.b64encode(arg_file.read())


def binary_tag_def(tag_str):
    """
    Parse a tag definition from the command line.  Return a dict that depends
    on the format of the string given:

     - 'key=value': {'Key': key, 'Value': value}
     - 'key=':      {'Key': key, 'Value': EMPTY}
     - 'key':       {'Key': key, 'Value': EMPTY}
    """
    if '=' in tag_str:
        (key, val) = tag_str.split('=', 1)
        return {'Key': key, 'Value': val or EMPTY}
    else:
        return {'Key': tag_str, 'Value': EMPTY}


def ternary_tag_def(tag_str):
    """
    Parse a tag definition from the command line.  Return a dict that depends
    on the format of the string given:

     - 'key=value': {'Key': key, 'Value': value}
     - 'key=':      {'Key': key, 'Value': EMPTY}
     - 'key':       {'Key': key}
    """
    if '=' in tag_str:
        (key, val) = tag_str.split('=', 1)
        return {'Key': key, 'Value': val or EMPTY}
    else:
        return {'Key': tag_str}


def delimited_list(delimiter, item_type=str):
    def _concrete_delimited_list(list_as_str):
        if isinstance(list_as_str, str) and len(list_as_str) > 0:
            return [item_type(item.strip()) for item in
                    list_as_str.split(delimiter) if len(item.strip()) > 0]
        else:
            return []
    return _concrete_delimited_list
