# Copyright 2013 Eucalyptus Systems, Inc.
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

from argparse import ArgumentTypeError


def autoscaling_filter_def(filter_str):
    filter_dict = {}
    pieces = filter_str.split(',')
    for piece in pieces:
        piece = piece.strip()
        if '=' not in piece:
            raise ArgumentTypeError(
                "invalid filter: each segment of '{0}' must have format "
                "KEY=VALUE".format(piece))
        key, val = piece.split('=', 1)
        filter_dict.setdefault(key.strip(), [])
        filter_dict[key.strip()].append(val.strip())
    filter_list = []
    for key, values in filter_dict.iteritems():
        filter_list.append({'Name': key, 'Values': values})
    return filter_list


def autoscaling_tag_def(tag_str):
    tag_dict = {}
    pieces = tag_str.split(',')
    for piece in pieces:
        piece = piece.strip()
        if '=' not in piece:
            raise ArgumentTypeError(
                "invalid tag definition: each segment of '{0}' must have "
                "format KEY=VALUE".format(piece))
        key, val = piece.split('=', 1)
        if key == 'k':
            tag_dict['Key'] = val
        elif key == 'id':
            tag_dict['ResourceId'] = val
        elif key == 't':
            tag_dict['ResourceType'] = val
        elif key == 'v':
            tag_dict['Value'] = val
        elif key == 'p':
            if val.lower() in ('true', 'false'):
                tag_dict['PropagateAtLaunch'] = val.lower()
            else:
                raise ArgumentTypeError(
                    "value for to 'p=' must be 'true' or 'false'")
        else:
            raise ArgumentTypeError(
                "unrecognized tag segment '{0}'".format(piece))
    if not tag_dict.get('Key'):
        raise ArgumentTypeError(
            "tag '{0}' must contain a 'k=' segment with a non-empty value")
    return tag_dict
