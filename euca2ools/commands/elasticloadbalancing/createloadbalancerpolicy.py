# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
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
from euca2ools.commands.elasticloadbalancing import ELBRequest
from requestbuilder import Arg


def attribute(attr_as_str):
    attr = {}
    for pair in attr_as_str.split(','):
        key, __, val = pair.partition('=')
        if key.strip() == 'name':
            attr['AttributeName'] = val.strip()
        elif key.strip() == 'value':
            attr['AttributeValue'] = val.strip()
        else:
            raise argparse.ArgumentTypeError(
                "attribute '{0}': '{1}' is not a valid part of an attribute "
                "(choose from " "'name', 'value')".format(attr_as_str,
                                                          key.strip()))
    if 'AttributeName' not in attr:
        raise argparse.ArgumentTypeError(
            "attribute '{0}': name is required".format(attr_as_str))
    if 'AttributeValue' not in attr:
        raise argparse.ArgumentTypeError(
            "attribute '{0}': value is required".format(attr_as_str))
    return attr


class CreateLoadBalancerPolicy(ELBRequest):
    DESCRIPTION = 'Add a new policy to a load balancer'
    ARGS = [Arg('LoadBalancerName', metavar='ELB',
                help='name of the load balancer to modify (required)'),
            Arg('--policy-name', dest='PolicyName', metavar='POLICY',
                required=True, help='name of the new policy (required)'),
            Arg('--policy-type', dest='PolicyTypeName', metavar='POLTYPE',
                required=True,
                help='''type of the new policy.  For a list of policy types,
                use eulb-describe-lb-policy-types.  (required)'''),
            Arg('-a', '--attribute', dest='PolicyAttributes.member',
                action='append', metavar='"name=NAME, value=VALUE"',
                type=attribute, help='''name and value for each attribute
                associated with the new policy.  Use this option multiple times
                to supply multiple attributes.''')]
