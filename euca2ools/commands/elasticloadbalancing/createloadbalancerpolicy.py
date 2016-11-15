# Copyright (c) 2013-2016 Hewlett Packard Enterprise Development LP
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

import sys

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.elasticloadbalancing import ELBRequest


def attribute(attr_as_str):
    attr = {}
    for pair in attr_as_str.split(','):
        key, val = pair.split('=', 1)
        if key.strip() == 'name':
            attr['AttributeName'] = val.strip()
        elif key.strip() == 'value':
            attr['AttributeValue'] = val.strip()
        else:
            raise ArgumentError(
                "attribute '{0}': '{1}' is not a valid part of an attribute "
                "(choose from 'name', 'value')".format(attr_as_str,
                                                       key.strip()))
    if 'AttributeName' not in attr:
        raise ArgumentError(
            "attribute '{0}': name is required".format(attr_as_str))
    if 'AttributeValue' not in attr:
        raise ArgumentError(
            "attribute '{0}': value is required".format(attr_as_str))
    return attr


def key_value_attribute(attr_as_str):
    if '=' not in attr_as_str:
        raise ArgumentError(
            "attribute '{0}' must have format NAME=VALUE".format(attr_as_str))
    key, val = attr_as_str.split('=', 1)
    if not key:
        raise ArgumentError(
            "attribute '{0}' must have a name".format(attr_as_str))
    return {'AttributeName': key.strip(), 'AttributeValue': val.strip()}


# Improve the output of argparse's TypeError/ValueError handling
key_value_attribute.__name__ = 'attribute'


class CreateLoadBalancerPolicy(ELBRequest):
    DESCRIPTION = 'Add a new policy to a load balancer'
    ARGS = [Arg('LoadBalancerName', metavar='ELB',
                help='name of the load balancer to modify (required)'),
            Arg('-n', '--policy-name', dest='PolicyName', metavar='POLICY',
                required=True, help='name of the new policy (required)'),
            Arg('-t', '--policy-type', dest='PolicyTypeName',
                metavar='POLTYPE', required=True,
                help='''type of the new policy.  For a list of policy types,
                use eulb-describe-lb-policy-types.  (required)'''),
            Arg('-a', '--attribute', dest='PolicyAttributes.member',
                action='append', metavar='"name=NAME, value=VALUE"',
                type=attribute, help='''name and value for each attribute
                associated with the new policy.  Use this option multiple times
                to supply multiple attributes.'''),
            Arg('-A', '--attributes', dest='new_attr_lists', route_to=None,
                metavar='NAME=VALUE,...', action='append',
                type=delimited_list(',', item_type=key_value_attribute),
                help='''a comma-delimited list of attribute names and values
                to associate with the new policy, each pair of which is
                separated by "=".  This is a more concise alternative to the
                -a/--attribute option.'''),
            Arg('--attributes-from-file', dest='attr_filename',
                metavar='FILE', route_to=None, help='''a file containing
                attribute names and values to associate with the new
                policy, one per line, each pair of which is separated by
                "=".  Lines that are blank or begin with "#" are ignored.''')]

    def preprocess(self):
        if not self.params.get('PolicyAttributes.member'):
            self.params['PolicyAttributes.member'] = []
        for attr_list in self.args.get('new_attr_lists') or []:
            self.params['PolicyAttributes.member'].extend(attr_list or [])
        if self.args.get('attr_filename'):
            if self.args['attr_filename'] == '-':
                attr_file = sys.stdin
            else:
                attr_file = open(self.args['attr_filename'])
            with attr_file:
                for line_no, line in enumerate(attr_file, 1):
                    if line.strip() and not line.startswith('#'):
                        try:
                            self.params['PolicyAttributes.member'].append(
                                key_value_attribute(line.strip()))
                        except ArgumentError as err:
                            raise ValueError(
                                'error on {0} line {1}: {2}'
                                .format(self.args['attr_filename'], line_no,
                                        err.args[0]))
