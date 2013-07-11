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

from euca2ools.commands.elasticloadbalancing import ELBRequest
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import TabifyingMixin


class ConfigureHealthCheck(ELBRequest, TabifyingMixin):
    DESCRIPTION = ('Configure health checking for instance registerd with a '
                   'load balancer')
    ARGS = [Arg('LoadBalancerName', metavar='ELB',
                help='name of the load balancer to modify (required)'),
            Arg('--healthy-threshold', dest='HealthCheck.HealthyThreshold',
                metavar='COUNT', type=int, required=True,
                help='''number of consecutive successful health checks that
                will mark instances as Healthy (required)'''),
            Arg('--interval', dest='HealthCheck.Interval', metavar='SECONDS',
                type=int, required=True,
                help='approximate interval between health checks (required)'),
            Arg('-t', '--target', dest='HealthCheck.Target',
                metavar='PROTOCOL:PORT[/PATH]', required=True,
                help='connection target for health checks (required)'),
            Arg('--timeout', dest='HealthCheck.Timeout', metavar='SECONDS',
                type=int, required=True,
                help='maximum health check duration (required)'),
            Arg('--unhealthy-threshold', dest='HealthCheck.UnhealthyThreshold',
                metavar='COUNT', type=int, required=True,
                help='''number of consecutive failed health checks that will
                mark instances as Unhealthy (required)''')]

    # noinspection PyExceptionInherit
    def configure(self):
        ELBRequest.configure(self)
        target = self.args['HealthCheck.Target']
        protocol, __, rest = target.partition(':')
        if not rest:
            raise ArgumentError('argument -t/--target: must have form '
                                'PROTOCOL:PORT[/PATH]')
        if protocol.lower() in ('http', 'https') and '/' not in rest:
            raise ArgumentError('argument -t/--target: path is required for '
                                "protocol '{0}'".format(protocol))

    def print_result(self, result):
        check = result.get('HealthCheck', {})
        print self.tabify(('HEALTH_CHECK', check.get('Target'),
                           check.get('Interval'), check.get('Timeout'),
                           check.get('HealthyThreshold'),
                           check.get('UnhealthyThreshold')))
