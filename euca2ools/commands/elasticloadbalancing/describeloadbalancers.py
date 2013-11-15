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
from requestbuilder.mixins import TabifyingMixin


class DescribeLoadBalancers(ELBRequest, TabifyingMixin):
    DESCRIPTION = 'Show information about load balancers'
    ARGS = [Arg('LoadBalancerNames.member', metavar='ELB', nargs='*',
                help='limit results to specific load balancers'),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the load balancers' info")]
    LIST_TAGS = ['LoadBalancerDescriptions', 'AvailabilityZones',
                 'BackendServerDescriptions', 'Instances',
                 'ListenerDescriptions', 'PolicyNames',
                 'AppCookieStickinessPolicies', 'LBCookieStickinessPolicies',
                 'OtherPolicies', 'SecurityGroups', 'Subnets']

    def print_result(self, result):
        for desc in result.get('LoadBalancerDescriptions', []):
            bits = ['LOAD_BALANCER',
                    desc.get('LoadBalancerName'),
                    desc.get('DNSName')]
            if self.args['show_long']:
                bits.append(desc.get('CanonicalHostedZoneName'))
                bits.append(desc.get('CanonicalHostedZoneNameID'))
                check = desc.get('HealthCheck')
                if check is not None:
                    check_str_bits = []
                    elem_map = (('interval', 'Interval'),
                                ('target', 'Target'),
                                ('timeout', 'Timeout'),
                                ('healthy-threshold', 'HealthyThreshold'),
                                ('unhealthy-threshold', 'UnhealthyThreshold'))
                    for name, xmlname in elem_map:
                        if check.get(xmlname):
                            check_str_bits.append(name + '=' + check[xmlname])
                    if len(check_str_bits) > 0:
                        bits.append('{' + ','.join(check_str_bits) + '}')
                    else:
                        bits.append(None)
                else:
                    bits.append(None)
                bits.append(','.join(zone for zone in
                                     desc.get('AvailabilityZones', [])))
                bits.append(','.join(net for net in desc.get('Subnets', [])))
                bits.append(desc.get('VPCId'))
                bits.append(','.join(instance.get('InstanceId') for instance in
                                     desc.get('Instances', [])))

                listeners = []
                for listenerdesc in desc.get('ListenerDescriptions', []):
                    listener = listenerdesc.get('Listener', {})
                    listener_str_bits = []
                    elem_map = (('protocol', 'Protocol'),
                                ('lb-port', 'LoadBalancerPort'),
                                ('instance-protocol', 'InstanceProtocol'),
                                ('instance-port', 'InstancePort'),
                                ('cert-id', 'SSLCertificateId'))
                    for name, xmlname in elem_map:
                        if listener.get(xmlname):
                            listener_str_bits.append(name + '=' +
                                                     listener[xmlname])
                    if listenerdesc.get('PolicyNames'):
                        listener_str_bits.append(
                            '{' + ','.join(listenerdesc['PolicyNames']) + '}')
                    listeners.append('{' + ','.join(listener_str_bits) + '}')
                if len(listeners) > 0:
                    bits.append(','.join(listeners))
                else:
                    bits.append(None)

                beservers = []
                for bedesc in desc.get('BackendServerDescriptions', []):
                    beserver_str_bits = []
                    if 'InstancePort' in bedesc:
                        beserver_str_bits.append('instance-port=' +
                                                 bedesc['InstancePort'])
                    if 'PolicyNames' in bedesc:
                        policies = ','.join(policy for policy in
                                            bedesc['PolicyNames'])
                        beserver_str_bits.append('policies={' + policies + '}')
                    beservers.append('{' + ','.join(beserver_str_bits) + '}')
                if len(beservers) > 0:
                    bits.append(','.join(beservers))
                else:
                    bits.append(None)

                all_policies = desc.get('Policies') or {}

                app_policies = all_policies.get(
                    'AppCookieStickinessPolicies') or {}
                app_policy_strs = ('{{policy-name={0},cookie-name={1}}}'
                                   .format(policy.get('PolicyName'),
                                           policy.get('CookieName'))
                                   for policy in app_policies)
                bits.append(','.join(app_policy_strs) or None)

                lb_policies = all_policies.get(
                    'LBCookieStickinessPolicies') or {}
                lb_policy_strs = ('{{policy-name={0},expiration-period={1}}}'
                                  .format(policy['PolicyName'],
                                          policy['CookieExpirationPeriod'])
                                  for policy in lb_policies)
                bits.append(','.join(lb_policy_strs) or None)

                other_policies = all_policies.get('OtherPolicies') or {}
                if other_policies:
                    bits.append('{' + ','.join(other_policies) + '}')
                else:
                    bits.append(None)

                group = desc.get('SourceSecurityGroup')
                if group:
                    bits.append('{{owner-alias={0},group-name={1}}}'.format(
                        group.get('OwnerAlias', ''),
                        group.get('GroupName', '')))
                else:
                    bits.append(None)

                if desc.get('SecurityGroups'):
                    bits.append('{' + ','.join(desc['SecurityGroups']) + '}')
                else:
                    bits.append(None)
            bits.append(desc.get('CreatedTime'))
            bits.append(desc.get('Scheme'))
            print self.tabify(bits)
