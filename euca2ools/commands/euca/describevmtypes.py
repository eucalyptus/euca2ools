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

from euca2ools.commands.euca import EucalyptusRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingCommand


class DescribeVmTypes(EucalyptusRequest, TabifyingCommand):
    DESCRIPTION = '[Eucalyptus only] Show information about instance types'
    ARGS = [Arg('VmTypes', metavar='INSTANCETYPE', nargs='*',
                help='limit results to specific instance types'),
            Arg('--by-zone', dest='by_zone', action='store_true',
                route_to=None,
                help='show info for each availability zone separately'),
            Arg('--show-capacity', dest='Availability', action='store_true',
                help='show info about instance capacity')]
    LIST_TAGS = ['vmTypeDetails', 'availability']

    def configure(self):
        EucalyptusRequest.configure(self)
        if self.args.get('by_zone', False):
            self.params['Availability'] = True


    def print_result(self, result):
        vmtype_names = []  # Keep an ordered list to deal with py2.6's lack
                           # of OrderedDict
        vmtypes = {}  # vmtype -> info and total capacity
        zones = {}  # zone -> vmtype -> info and zone capacity
        for vmtype in result.get('vmTypeDetails', []):
            vmtype_names.append(vmtype['name'])
            vmtypes[vmtype['name']] = {'cpu': vmtype.get('cpu'),
                                       'memory': vmtype.get('memory'),
                                       'disk': vmtype.get('disk'),
                                       'available': 0,
                                       'max': 0}
            if self.params.get('Availability', False):
                for zone in vmtype.get('availability', []):
                    available = int(zone.get('available', 0))
                    max_ = int(zone.get('max', 0))
                    vmtypes[vmtype['name']]['available'] += available
                    vmtypes[vmtype['name']]['max'] += max_
                    zones.setdefault(zone['zoneName'], {})
                    zones[zone['zoneName']][vmtype['name']] = {
                        'cpu': vmtype.get('cpu'),
                        'memory': vmtype.get('memory'),
                        'disk': vmtype.get('disk'),
                        'available': available,
                        'max': max_}


        if self.args.get('by_zone'):
            for zone, zone_vmtypes in sorted(zones.iteritems()):
                print self.tabify(('AVAILABILITYZONE', zone))
                self._print_vmtypes(zone_vmtypes, vmtype_names)
                print
        else:
            self._print_vmtypes(vmtypes, vmtype_names)

    def _print_vmtypes(self, vmtypes, vmtype_names):
        # Fields and column headers
        fields = {'name': 'Name',
                  'cpu': 'CPUs',
                  'memory': 'Memory (MB)',
                  'disk': 'Disk (GB)',
                  'used': 'Used',
                  'total': 'Total',
                  'used_pct': 'Used %'}
        field_lengths = dict((field, len(header)) for field, header
                              in fields.iteritems())
        vmtype_infos = []
        for vmtype_name in vmtype_names:
            total = int(vmtypes[vmtype_name].get('max', 0))
            used = total - int(vmtypes[vmtype_name].get('available', 0))
            if total != 0:
                used_pct = '{0:.0%}'.format(float(used) / float(total))
            else:
                used_pct = ''
            vmtype_info = {'name': vmtype_name,
                           'cpu': vmtypes[vmtype_name].get('cpu'),
                           'memory': vmtypes[vmtype_name].get('memory'),
                           'disk': vmtypes[vmtype_name].get('disk'),
                           'used': used,
                           'total': total,
                           'used_pct': used_pct}
            vmtype_infos.append(vmtype_info)
            for field in fields:
                if len(str(vmtype_info[field])) > field_lengths[field]:
                    field_lengths[field] = len(str(vmtype_info[field]))
        type_template = ('{{name:<{name}}}  {{cpu:>{cpu}}}  '
                         '{{memory:>{memory}}}  {{disk:>{disk}}}')
        if self.args.get('Availability', False):
            type_template += ('  {{used:>{used}}} / {{total:>{total}}}  '
                              '{{used_pct:>{used_pct}}}')
        type_template = type_template.format(**field_lengths)

        print 'INSTANCETYPE\t', type_template.format(**fields)
        for vmtype_info in vmtype_infos:
            print 'INSTANCETYPE\t', type_template.format(**vmtype_info)
