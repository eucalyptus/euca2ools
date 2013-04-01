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

from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.elasticloadbalancing import ELBRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingCommand


def instance(inst_as_str):
    return {'InstanceId': inst_as_str}


class DescribeInstanceHealth(ELBRequest, TabifyingCommand):
    DESCRIPTION = 'Show the state of instances registered with a load balancer'
    ARGS = [Arg('LoadBalancerName', metavar='ELB', help='''name of the load
                balancer the to describe instances for (required)'''),
            Arg('--instances', dest='Instances.member',
                metavar='INSTANCE1,INSTANCE2,...',
                type=delimited_list(',', item_type=instance),
                help='limit results to specific instances'),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the instances' info")]
    LIST_TAGS = ['InstanceStates']

    def print_result(self, result):
        for instance in result.get('InstanceStates', []):
            bits = ['INSTANCE', instance.get('InstanceId'),
                    instance.get('State')]
            if self.args['show_long']:
                bits.append(instance.get('Description'))
                bits.append(instance.get('ReasonCode'))
            print self.tabify(bits)
