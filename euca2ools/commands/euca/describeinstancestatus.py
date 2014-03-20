# Copyright 2013-2014 Eucalyptus Systems, Inc.
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

import dateutil.parser
from requestbuilder import Arg, Filter

from euca2ools.commands.euca import EucalyptusRequest


class DescribeInstanceStatus(EucalyptusRequest):
    DESCRIPTION = 'Show information about instance status and scheduled events'
    ARGS = [Arg('InstanceId', metavar='INSTANCE', nargs='*',
                help='limit results to specific instances'),
            Arg('--hide-healthy', action='store_true', route_to=None,
                help='hide instances where all status checks pass'),
            Arg('--include-all-instances', dest='IncludeAllInstances',
                action='store_true',
                help='show all instances, not just those that are running')]
    FILTERS = [Filter('availability-zone'),
               Filter('event.code',
                      choices=('instance-reboot', 'instance-retirement',
                               'instance-stop', 'system-maintenance',
                               'instance-retirement'),
                      help='the code identifying the type of event'),
               Filter('event.description', help="an event's description"),
               Filter('event.not-after',
                      help="an event's latest possible end time"),
               Filter('event.not-before',
                      help="an event's earliest possible start time"),
               Filter('instance-state-code', type=int,
                      help='numeric code identifying instance state'),
               Filter('instance-state-name', help='instance state'),
               Filter('instance-status.status', help="instance's status",
                      choices=('ok', 'impaired', 'initializing',
                               'insufficient-data', 'not-applicable')),
               Filter('instance-status.reachability',
                      choices=('passed', 'failed', 'initializing',
                               'insufficient-data'),
                      help="instance's reachability status"),
               Filter('system-status.status', help="instance's system status",
                      choices=('ok', 'impaired', 'initializing',
                               'insufficient-data', 'not-applicable')),
               Filter('system-status.reachability',
                      choices=('passed', 'failed', 'initializing',
                               'insufficient-data'),
                      help="instance's system reachability status")]
    LIST_TAGS = ['instanceStatusSet', 'details', 'eventsSet']

    def print_result(self, result):
        for sset in result.get('instanceStatusSet') or []:
            if (self.args.get('hide_healthy', False) and
                    sset.get('systemStatus', {}).get('status') == 'ok' and
                    sset.get('instanceStatus', {}).get('status') == 'ok'):
                continue
            print self.tabify((
                'INSTANCE', sset.get('instanceId'),
                sset.get('availabilityZone'),
                sset.get('instanceState', {}).get('name'),
                sset.get('instanceState', {}).get('code'),
                sset.get('instanceStatus', {}).get('status'),
                sset.get('systemStatus', {}).get('status'),
                get_retirement_status(sset), get_retirement_date(sset)))
            for sstatus in sset.get('systemStatus', {}).get('details') or []:
                print self.tabify((
                    'SYSTEMSTATUS', sstatus.get('name'),
                    sstatus.get('status'), sstatus.get('impairedSince')))
            for istatus in sset.get('systemStatus', {}).get('details') or []:
                print self.tabify((
                    'INSTANCESTATUS', istatus.get('name'),
                    istatus.get('status'), istatus.get('impairedSince')))
            for event in sset.get('eventsSet') or []:
                print self.tabify((
                    'EVENT', event.get('code'), event.get('notBefore'),
                    event.get('notAfter'), event.get('description')))


def get_retirement_date(status_set):
    retirement_date = None
    for event in status_set.get('eventsSet', []):
        event_start = event.get('notBefore')
        if event_start is not None:
            if retirement_date is None:
                retirement_date = event_start
            elif (dateutil.parser.parse(event.get(event_start)) <
                  dateutil.parser.parse(retirement_date)):
                retirement_date = event_start
    return retirement_date


def get_retirement_status(status_set):
    # This is more or less a guess, since retirement status isn't part of the
    # EC2 API.  The value seems to be chosen entirely client-side.
    if len(status_set.get('eventsSet', [])) > 0:
        return 'retiring'
    else:
        return 'active'
