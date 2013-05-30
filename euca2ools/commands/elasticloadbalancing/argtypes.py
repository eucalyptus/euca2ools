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

import argparse


def listener(listener_str):
    pairs = {}
    for pair_str in listener_str.strip().split(','):
        if pair_str:
            try:
                key, val = pair_str.split('=')
            except ValueError:
                raise argparse.ArgumentTypeError(
                    "listener '{0}': element '{1}' must have format KEY=VALUE"
                    .format(listener_str, pair_str))
            pairs[key.strip()] = val.strip()

    extra_keys = (set(pairs.keys()) -
                  set(('protocol', 'lb-port', 'instance-port',
                       'instance-protocol', 'cert-id')))
    if len(extra_keys) > 0:
        raise argparse.ArgumentTypeError(
            "listener '{0}': invalid element(s): {1}".format(listener_str,
                ', '.join("'{0}'".format(key) for key in extra_keys)))

    listener_dict = {}
    if 'protocol' in pairs:
        if pairs['protocol'] in ('HTTP', 'HTTPS', 'SSL', 'TCP'):
            listener_dict['Protocol'] = pairs['protocol']
        else:
            raise argparse.ArgumentTypeError(
                "listener '{0}': protocol '{1}' is invalid (choose from "
                "'HTTP', 'HTTPS', 'SSL', 'TCP')"
                .format(listener_str, pairs['protocol']))
    else:
        raise argparse.ArgumentTypeError(
            "listener '{0}': protocol is required".format(listener_str))
    if 'lb-port' in pairs:
        try:
            listener_dict['LoadBalancerPort'] = int(pairs['lb-port'])
        except ValueError:
            raise argparse.ArgumentTypeError(
                "listener '{0}': lb-port must be an integer"
                .format(listener_str))
    else:
        raise argparse.ArgumentTypeError(
            "listener '{0}': lb-port is required".format(listener_str))
    if 'instance-port' in pairs:
        try:
            listener_dict['InstancePort'] = int(pairs['instance-port'])
        except ValueError:
            raise argparse.ArgumentTypeError(
                "listener '{0}': instance-port must be an integer"
                .format(listener_str))
    else:
        raise argparse.ArgumentTypeError(
            "listener '{0}': instance-port is required".format(listener_str))
    if 'instance-protocol' in pairs:
        if pairs['instance-protocol'] in ('HTTP', 'HTTPS'):
            if pairs['protocol'] not in ('HTTP', 'HTTPS'):
                raise argparse.ArgumentTypeError(
                    "listener '{0}': instance-protocol must be 'HTTP' or "
                    "'HTTPS' when protocol is 'HTTP' or 'HTTPS'"
                    .format(listener_str))
        elif pairs['instance-protocol'] in ('SSL', 'TCP'):
            if pairs['protocol'] not in ('SSL', 'TCP'):
                raise argparse.ArgumentTypeError(
                    "listener '{0}': instance-protocol must be 'SSL' or "
                    "'TCP' when protocol is 'SSL' or 'TCP'"
                    .format(listener_str))
        else:
            raise argparse.ArgumentTypeError(
                "listener '{0}': instance-protocol '{1}' is invalid (choose "
                "from 'HTTP', 'HTTPS', 'SSL', 'TCP')"
                .format(listener_str, pairs['instance-protocol']))
        listener_dict['InstanceProtocol'] = pairs['instance-protocol']
    if 'cert-id' in pairs:
        listener_dict['SSLCertificateId'] = pairs['cert-id']
    return listener_dict
