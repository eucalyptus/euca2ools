# Copyright 2015 Eucalyptus Systems, Inc.
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

from requestbuilder import Arg

from euca2ools.commands.elasticloadbalancing import ELBRequest


def key_value(arg_val):
    if '=' not in arg_val:
        raise argparse.ArgumentTypeError('invalid ATTR=VALUE pair: {0}'
                                         .format(arg_val))
    return dict([arg_val.split('=', 1)])


class ModifyLoadBalancerAttributes(ELBRequest):
    DESCRIPTION = "Modify a load balancer's attributes"
    ARGS = [Arg('LoadBalancerName', metavar='ELB',
                help='the load balancer to describe (required)'),
            Arg('attrs', metavar='ATTR=VALUE', nargs='+', type=key_value,
                route_to=None, help='''name and new value of each
                attribute to modify (required)''')]

    def preprocess(self):
        self.params['LoadBalancerAttributes'] = {}
        for attr in self.args['attrs']:
            self.params['LoadBalancerAttributes'].update(attr)
