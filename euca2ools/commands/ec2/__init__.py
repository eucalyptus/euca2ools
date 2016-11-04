# Copyright (c) 2009-2016 Hewlett Packard Enterprise Development LP
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
import io
from operator import itemgetter
import os.path
import six
import socket
from string import Template
import sys

import lxml.etree
from requestbuilder import Arg
import requestbuilder.auth.aws
from requestbuilder.exceptions import ArgumentError, AuthError, ClientError
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.request import AWSQueryRequest
from requestbuilder.service import BaseService
import requests.exceptions

from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from euca2ools.util import add_fake_region_name


class EC2(BaseService):
    NAME = 'ec2'
    DESCRIPTION = 'Elastic compute cloud service'
    API_VERSION = '2015-10-01'
    REGION_ENVVAR = ('EUCA_DEFAULT_REGION', 'AWS_DEFAULT_REGION')
    URL_ENVVAR = 'EC2_URL'

    ARGS = [Arg('-U', '--url', metavar='URL',
                help='compute service endpoint URL')]

    def configure(self):
        requestbuilder.service.BaseService.configure(self)
        add_fake_region_name(self)

    # pylint: disable=no-self-use
    def handle_http_error(self, response):
        raise AWSError(response)
    # pylint: enable=no-self-use


class EC2Request(AWSQueryRequest, TabifyingMixin):
    SUITE = Euca2ools
    SERVICE_CLASS = EC2
    AUTH_CLASS = requestbuilder.auth.aws.HmacV4Auth
    METHOD = 'POST'

    def __init__(self, **kwargs):
        AWSQueryRequest.__init__(self, **kwargs)

    def print_resource_tag(self, resource_tag, resource_id):
        resource_type = RESOURCE_TYPE_MAP.lookup(resource_id)
        print self.tabify(['TAG', resource_type, resource_id,
                           resource_tag.get('key'), resource_tag.get('value')])

    def print_reservation(self, reservation):
        res_line = ['RESERVATION', reservation['reservationId'],
                    reservation.get('ownerId')]
        # group.get('entry') is a workaround for a CLC bug
        group_ids = [group.get('groupName') or group.get('groupId') or
                     group.get('entry') or ''
                     for group in reservation['groupSet']]
        res_line.append(', '.join(group_ids))
        print self.tabify(res_line)
        for instance in sorted(reservation.get('instancesSet') or [],
                               key=itemgetter('launchTime')):
            self.print_instance(instance)

    def print_instance(self, instance):
        instance_line = ['INSTANCE']
        for key in ['instanceId', 'imageId', 'dnsName', 'privateDnsName']:
            instance_line.append(instance.get(key))
        instance_line.append(instance.get('instanceState', {}).get('name'))
        instance_line.append(instance.get('keyName'))
        instance_line.append(instance.get('amiLaunchIndex'))
        instance_line.append(','.join([code['productCode'] for code in
                                       instance.get('productCodes', [])]))
        instance_line.append(instance.get('instanceType'))
        instance_line.append(instance.get('launchTime'))
        instance_line.append(instance.get('placement', {}).get(
            'availabilityZone'))
        instance_line.append(instance.get('kernelId'))
        instance_line.append(instance.get('ramdiskId'))
        instance_line.append(instance.get('platform'))
        if instance.get('monitoring'):
            instance_line.append('monitoring-' +
                                 instance['monitoring'].get('state'))
        else:
            # noinspection PyTypeChecker
            instance_line.append(None)
        instance_line.append(instance.get('ipAddress'))
        instance_line.append(instance.get('privateIpAddress'))
        instance_line.append(instance.get('vpcId'))
        instance_line.append(instance.get('subnetId'))
        instance_line.append(instance.get('rootDeviceType'))
        instance_line.append(instance.get('instanceLifecycle'))
        instance_line.append(instance.get('showInstanceRequestId'))
        # noinspection PyTypeChecker
        instance_line.append(None)  # Should be the license, but where is it?
        instance_line.append(instance.get('placement', {}).get('groupName'))
        instance_line.append(instance.get('virtualizationType'))
        instance_line.append(instance.get('hypervisor'))
        instance_line.append(instance.get('clientToken'))
        instance_line.append(','.join([group['groupId'] for group in
                                       instance.get('groupSet', [])]))
        instance_line.append(instance.get('placement', {}).get('tenancy'))
        instance_line.append(instance.get('ebsOptimized'))
        instance_line.append(instance.get('iamInstanceProfile', {}).get('arn'))
        instance_line.append(instance.get('architecture'))
        print self.tabify(instance_line)

        for blockdev in instance.get('blockDeviceMapping', []):
            self.print_blockdevice(blockdev)

        for nic in instance.get('networkInterfaceSet', []):
            self.print_interface(nic)

        for tag in instance.get('tagSet', []):
            self.print_resource_tag(tag, instance.get('instanceId'))

    def print_blockdevice(self, blockdev):
        # Block devices belong to instances
        print self.tabify(('BLOCKDEVICE', blockdev.get('deviceName'),
                           blockdev.get('ebs', {}).get('volumeId'),
                           blockdev.get('ebs', {}).get('attachTime'),
                           blockdev.get('ebs', {}).get('deleteOnTermination'),
                           blockdev.get('ebs', {}).get('volumeType'),
                           blockdev.get('ebs', {}).get('iops')))

    def print_blockdevice_mapping(self, mapping):
        # Block device mappings belong to images
        if mapping.get('virtualName'):
            print self.tabify(('BLOCKDEVICEMAPPING', 'EPHEMERAL',
                               mapping.get('deviceName'),
                               mapping.get('virtualName')))
        else:
            ebs = mapping.get('ebs') or {}
            print self.tabify(('BLOCKDEVICEMAPPING', 'EBS',
                               mapping.get('deviceName'),
                               ebs.get('snapshotId'), ebs.get('volumeSize'),
                               ebs.get('deleteOnTermination'),
                               ebs.get('volumeType'), ebs.get('iops')))

    def print_attachment(self, attachment):
        print self.tabify(['ATTACHMENT', attachment.get('volumeId'),
                           attachment.get('instanceId'),
                           attachment.get('device'),
                           attachment.get('status'),
                           attachment.get('attachTime')])

    def print_vpc(self, vpc):
        print self.tabify(('VPC', vpc.get('vpcId'), vpc.get('state'),
                           vpc.get('cidrBlock'), vpc.get('dhcpOptionsId'),
                           vpc.get('instanceTenancy'), vpc.get('isDefault')))
        for tag in vpc.get('tagSet') or []:
            self.print_resource_tag(tag, vpc.get('vpcId'))

    def print_internet_gateway(self, igw):
        print self.tabify(('INTERNETGATEWAY', igw.get('internetGatewayId')))
        for attachment in igw.get('attachmentSet') or []:
            print self.tabify(('ATTACHMENT', attachment.get('vpcId'),
                               attachment.get('state')))
        for tag in igw.get('tagSet') or []:
            self.print_resource_tag(tag, igw.get('internetGatewayId'))

    def print_nat_gateway(self, natgw):
        print self.tabify(('NATGATEWAY', natgw.get('natGatewayId'),
                           natgw.get('state'), natgw.get('subnetId'),
                           natgw.get('vpcId'), natgw.get('failureCode'),
                           natgw.get('failureMessage'),
                           natgw.get('createTime'),
                           natgw.get('deleteTime'),))
        for address_set in natgw.get('natGatewayAddressSet') or []:
            print self.tabify(('NATGATEWAYADDRESSES',
                               address_set.get('allocationId'),
                               address_set.get('networkInterfaceId'),
                               address_set.get('publicIp'),
                               address_set.get('privateIp')))

    def print_peering_connection(self, pcx):
        status = pcx.get('status') or {}
        print self.tabify(('VPCPEERINGCONNECTION',
                           pcx.get('vpcPeeringConnectionId'),
                           pcx.get('expirationTime'),
                           '{0}: {1}'.format(status.get('code'),
                                             status.get('message'))))
        requester = pcx.get('requesterVpcInfo') or {}
        print self.tabify(('REQUESTERVPCINFO', requester.get('vpcId'),
                           requester.get('cidrBlock'),
                           requester.get('ownerId')))
        accepter = pcx.get('accepterVpcInfo') or {}
        print self.tabify(('ACCEPTERVPCINFO', accepter.get('vpcId'),
                           accepter.get('cidrBlock'), accepter.get('ownerId')))
        for tag in pcx.get('tagSet') or []:
            self.print_resource_tag(tag, pcx.get('vpcPeeringConnectionId'))

    def print_subnet(self, subnet):
        print self.tabify(('SUBNET', subnet.get('subnetId'),
                           subnet.get('state'), subnet.get('vpcId'),
                           subnet.get('cidrBlock'),
                           subnet.get('availableIpAddressCount'),
                           subnet.get('availabilityZone'),
                           subnet.get('defaultForAz'),
                           subnet.get('mapPublicIpOnLaunch')))
        for tag in subnet.get('tagSet') or []:
            self.print_resource_tag(tag, subnet.get('subnetId'))

    def print_network_acl(self, acl):
        if acl.get('default').lower() == 'true':
            default = 'default'
        else:
            default = ''
        print self.tabify(('NETWORKACL', acl.get('networkAclId'),
                           acl.get('vpcId'), default))
        for entry in acl.get('entrySet') or []:
            if entry.get('egress').lower() == 'true':
                direction = 'egress'
            else:
                direction = 'ingress'
            protocol = entry.get('protocol')
            port_map = {-1: 'all', 1: 'icmp', 6: 'tcp', 17: 'udp', 132: 'sctp'}
            try:
                protocol = port_map.get(int(protocol), int(protocol))
            except ValueError:
                pass
            if 'icmpTypeCode' in entry:
                from_port = entry.get('icmpTypeCode', {}).get('code')
                to_port = entry.get('icmpTypeCode', {}).get('type')
            else:
                from_port = entry.get('portRange', {}).get('from')
                to_port = entry.get('portRange', {}).get('to')
            print self.tabify(('ENTRY', direction, entry.get('ruleNumber'),
                               entry.get('ruleAction'), entry.get('cidrBlock'),
                               protocol, from_port, to_port))
        for assoc in acl.get('associationSet') or []:
            print self.tabify(('ASSOCIATION',
                               assoc.get('networkAclAssociationId'),
                               assoc.get('subnetId')))
        for tag in acl.get('tagSet') or []:
            self.print_resource_tag(tag, acl.get('networkAclId'))

    def print_route_table(self, table):
        print self.tabify(('ROUTETABLE', table.get('routeTableId'),
                           table.get('vpcId')))
        for route in table.get('routeSet') or []:
            target = (route.get('gatewayId') or route.get('instanceId') or
                      route.get('networkInterfaceId') or
                      route.get('natGatewayId') or
                      route.get('vpcPeeringConnectionId'))
            print self.tabify((
                'ROUTE', target, route.get('state'),
                route.get('destinationCidrBlock'), route.get('origin')))
        for vgw in table.get('propagatingVgwSet') or []:
            print self.tabify(('PROPAGATINGVGW', vgw.get('gatewayID')))
        for assoc in table.get('associationSet') or []:
            if (assoc.get('main') or '').lower() == 'true':
                main = 'main'
            else:
                main = ''
            print self.tabify(('ASSOCIATION',
                               assoc.get('routeTableAssociationId'),
                               assoc.get('subnetId'), main))
        for tag in table.get('tagSet') or []:
            self.print_resource_tag(tag, table.get('routeTableId'))

    def print_interface(self, nic):
        nic_info = [nic.get(attr) for attr in (
            'networkInterfaceId', 'subnetId', 'vpcId', 'ownerId', 'status',
            'privateIpAddress', 'privateDnsName', 'sourceDestCheck')]
        print self.tabify(['NETWORKINTERFACE'] + nic_info)
        if nic.get('attachment'):
            attachment_info = [nic['attachment'].get(attr) for attr in (
                'instanceId', 'attachmentId', 'deviceIndex', 'status',
                'attachTime', 'deleteOnTermination')]
            print self.tabify(['ATTACHMENT'] + attachment_info)
        privaddresses = nic.get('privateIpAddressesSet', [])
        if nic.get('association'):
            association = nic['association']
            # The EC2 tools apparently print private IP info in the
            # association even though that info doesn't appear there
            # in the response, so we have to look it up elsewhere.
            for privaddress in privaddresses:
                if (privaddress.get('association', {}).get('publicIp') ==
                        association.get('publicIp')):
                    # Found a match
                    break
            else:
                privaddress = None
            print self.tabify(('ASSOCIATION', association.get('publicIp'),
                               association.get('ipOwnerId'),
                               privaddress.get('privateIpAddress')))
        for group in nic.get('groupSet', []):
            print self.tabify(('GROUP', group.get('groupId'),
                               group.get('groupName')))
        for privaddress in privaddresses:
            if privaddress.get('primary').lower() == 'true':
                primary = 'primary'
            else:
                primary = None
            print self.tabify(('PRIVATEIPADDRESS',
                               privaddress.get('privateIpAddress'),
                               privaddress.get('privateDnsName'), primary))
        for tag in nic.get('tagSet') or []:
            self.print_resource_tag(tag, nic.get('networkInterfaceId'))

    def print_customer_gateway(self, cgw):
        print self.tabify(('CUSTOMERGATEWAY', cgw.get('customerGatewayId'),
                           cgw.get('state'), cgw.get('type'),
                           cgw.get('ipAddress'), cgw.get('bgpAsn')))
        for tag in cgw.get('tagSet', []):
            self.print_resource_tag(tag, cgw.get('customerGatewayId'))

    def print_vpn_gateway(self, vgw):
        print self.tabify(('VPNGATEWAY', vgw.get('vpnGatewayId'),
                           vgw.get('state'), vgw.get('availabilityZone'),
                           vgw.get('type')))
        for attachment in vgw.get('attachments'):
            print self.tabify(('VGWATTACHMENT', attachment.get('vpcId'),
                               attachment.get('state')))
        for tag in vgw.get('tagSet', []):
            self.print_resource_tag(tag, vgw.get('vpnGatewayId'))

    def print_vpn_connection(self, vpn, show_conn_info=False,
                             stylesheet=None):
        print self.tabify(('VPNCONNECTION', vpn.get('vpnConnectionId'),
                           vpn.get('type'), vpn.get('customerGatewayId'),
                           vpn.get('vpnGatewayId'), vpn.get('state')))
        if show_conn_info and vpn.get('customerGatewayConfiguration'):
            if stylesheet is None:
                print vpn.get('customerGatewayConfiguration')
            else:
                if (stylesheet.startswith('http://') or
                        stylesheet.startswith('https://')):
                    self.log.info('fetching connection info stylesheet from %s',
                                  stylesheet)
                    response = requests.get(stylesheet)
                    try:
                        response.raise_for_status()
                    except requests.exceptions.HTTPError as err:
                        raise ClientError('failed to fetch stylesheet: {0}'
                                          .format(str(err)))
                    xslt_root = lxml.etree.XML(response.text)
                else:
                    if stylesheet.startswith('file://'):
                        stylesheet = stylesheet[7:]
                    self.log.info('using connection info stylesheet %s',
                                  stylesheet)
                    with open(stylesheet) as stylesheet_file:
                        xslt_root = lxml.etree.parse(stylesheet_file)
                transform = lxml.etree.XSLT(xslt_root)
                conn_info_root = lxml.etree.parse(io.BytesIO(
                    vpn.get('customerGatewayConfiguration')))
                print transform(conn_info_root)
        for tag in vpn.get('tagSet') or []:
            self.print_resource_tag(tag, vpn.get('vpnConnectionId'))

    def print_dhcp_options(self, dopt):
        print self.tabify(('DHCPOPTIONS', dopt.get('dhcpOptionsId')))
        for option in dopt.get('dhcpConfigurationSet') or {}:
            values = [val_dict.get('value')
                      for val_dict in option.get('valueSet')]
            print self.tabify(('OPTION', option.get('key'), ','.join(values)))
        for tag in dopt.get('tagSet', []):
            self.print_resource_tag(tag, dopt.get('dhcpOptionsId'))

    def print_volume(self, volume):
        vol_bits = ['VOLUME']
        for attr in ('volumeId', 'size', 'snapshotId', 'availabilityZone',
                     'status', 'createTime'):
            vol_bits.append(volume.get(attr))
        vol_bits.append(volume.get('volumeType') or 'standard')
        vol_bits.append(volume.get('iops'))
        print self.tabify(vol_bits)
        for attachment in volume.get('attachmentSet', []):
            self.print_attachment(attachment)
        for tag in volume.get('tagSet', []):
            self.print_resource_tag(tag, volume.get('volumeId'))

    def print_snapshot(self, snap):
        print self.tabify(['SNAPSHOT', snap.get('snapshotId'),
                           snap.get('volumeId'), snap.get('status'),
                           snap.get('startTime'), snap.get('progress'),
                           snap.get('ownerId'), snap.get('volumeSize'),
                           snap.get('description')])
        for tag in snap.get('tagSet', []):
            self.print_resource_tag(tag, snap.get('snapshotId'))

    def print_bundle_task(self, task):
        bucket = task.get('storage', {}).get('S3', {}).get('bucket')
        prefix = task.get('storage', {}).get('S3', {}).get('prefix')
        if bucket and prefix:
            manifest = '{0}/{1}.manifest.xml'.format(bucket, prefix)
        else:
            manifest = None
        print self.tabify(['BUNDLE', task.get('bundleId'),
                           task.get('instanceId'), bucket, prefix,
                           task.get('startTime'), task.get('updateTime'),
                           task.get('state'), task.get('progress'), manifest])

    def print_conversion_task(self, task):
        task_bits = []
        if task.get('importVolume'):
            task_bits.extend(('TaskType', 'IMPORTVOLUME'))
        if task.get('importInstance'):
            task_bits.extend(('TaskType', 'IMPORTINSTANCE'))
        if task.get('conversionTaskId'):
            task_bits.append('TaskId')
            task_bits.append(task.get('conversionTaskId'))
        if task.get('expirationTime'):
            task_bits.append('ExpirationTime')
            task_bits.append(task['expirationTime'])
        if task.get('state'):
            task_bits.append('Status')
            task_bits.append(task['state'])
        if task.get('statusMessage'):
            task_bits.append('StatusMessage')
            task_bits.append(task['statusMessage'])

        if task.get('importVolume'):
            print self.tabify(task_bits)
            self.__print_import_disk(task['importVolume'])
        if task.get('importInstance'):
            if task['importInstance'].get('instanceId'):
                task_bits.extend(('InstanceID',
                                  task['importInstance']['instanceId']))
            print self.tabify(task_bits)
            for volume in task['importInstance'].get('volumes') or []:
                self.__print_import_disk(volume)

    def __print_import_disk(self, container):
        disk_bits = ['DISKIMAGE']
        image = container.get('image') or {}
        volume = container.get('volume') or {}
        if image.get('format'):
            disk_bits.extend(('DiskImageFormat', image['format']))
        if image.get('size'):
            disk_bits.extend(('DiskImageSize', image['size']))
        if volume.get('id'):
            disk_bits.extend(('VolumeId', volume['id']))
        if volume.get('size'):
            disk_bits.extend(('VolumeSize', volume['size']))
        if container.get('availabilityZone'):
            disk_bits.extend(('AvailabilityZone',
                              container['availabilityZone']))
        if container.get('bytesConverted'):
            disk_bits.extend(('ApproximateBytesConverted',
                              container['bytesConverted']))
        if container.get('status'):
            # This is the status of the volume for an ImportInstance operation
            disk_bits.extend(('Status', container.get('status')))
        if container.get('statusMessage'):
            disk_bits.extend(('StatusMessage', container.get('statusMessage')))
        print self.tabify((disk_bits))

    def process_port_cli_args(self):
        """
        Security group and network ACL rule commands need to be able to
        to parse "-1:-1" before argparse can see it because of Python
        bug 9334, which causes argparse to treat it as a nonexistent
        option name and not an option value.  This method wraps
        process_cli_args in such a way that values beginning with "-1"
        are preserved.
        """
        saved_sys_argv = list(sys.argv)

        def parse_neg_one_value(opt_name):
            if opt_name in sys.argv:
                index = sys.argv.index(opt_name)
                if (index < len(sys.argv) - 1 and
                        sys.argv[index + 1].startswith('-1')):
                    opt_val = sys.argv[index + 1]
                    del sys.argv[index:index + 2]
                    return opt_val

        icmp_type_code = (parse_neg_one_value('-t') or
                          parse_neg_one_value('--icmp-type-code'))
        port_range = (parse_neg_one_value('-p') or
                      parse_neg_one_value('--port-range'))
        EC2Request.process_cli_args(self)
        if icmp_type_code:
            self.args['icmp_type_code'] = icmp_type_code
        if port_range:
            self.args['port_range'] = port_range
        sys.argv = saved_sys_argv


class _ResourceTypeMap(object):
    _prefix_type_map = {
        'eipalloc': 'allocation-id',
        'bun':    'bundle',  # technically a bundle *task*
        'import': 'conversion-task',  # this is a guess
        'cgw':    'customer-gateway',
        'dopt':   'dhcp-options',
        'export': 'export-task',  # this is a guess
        'aki':    'image',
        'ami':    'image',
        'ari':    'image',
        'eki':    'image',
        'emi':    'image',
        'eri':    'image',
        'i':      'instance',
        'igw':    'internet-gateway',
        'acl':    'network-acl',
        'eni':    'network-interface',
        'xxx':    'reserved-instances',  # reserved instance IDs are UUIDs
        'rtb':    'route-table',
        'sg':     'security-group',
        'snap':   'snapshot',
        'sir':    'spot-instances-request',
        'subnet': 'subnet',
        'vol':    'volume',
        'vpc':    'vpc',
        'pcx':    'vpc-peering-connection',
        'vpn':    'vpn-connection',
        'vgw':    'vpn-gateway'}

    def lookup(self, item):
        if not isinstance(item, basestring):
            raise TypeError('argument type must be str')
        for prefix in self._prefix_type_map:
            if item.startswith(prefix + '-'):
                return self._prefix_type_map[prefix]

    def __iter__(self):
        return iter(set(self._prefix_type_map.values()))

RESOURCE_TYPE_MAP = _ResourceTypeMap()


def parse_ports(protocol, port_range=None, icmp_type_code=None):
    # This function's error messages make assumptions about arguments'
    # names, but currently all of its callers agree on them.  If that
    # changes then please fix this.
    from_port = None
    to_port = None
    if str(protocol).lower() in ('icmp', '1'):
        if port_range:
            raise ArgumentError('argument -p/--port-range: not compatible '
                                'with protocol "{0}"'.format(protocol))
        if not icmp_type_code:
            icmp_type_code = '-1:-1'
        types = icmp_type_code.split(':')
        if len(types) == 2:
            try:
                from_port = int(types[0])
                to_port = int(types[1])
            except ValueError:
                raise ArgumentError('argument -t/--icmp-type-code: value '
                                    'must have format "1:2"')
        else:
            raise ArgumentError('argument -t/--icmp-type-code: value '
                                'must have format "1:2"')
        if from_port < -1 or to_port < -1:
            raise ArgumentError('argument -t/--icmp-type-code: ICMP type, '
                                'code must be at least -1')
    elif str(protocol).lower() in ('tcp', '6', 'udp', '17'):
        if icmp_type_code:
            raise ArgumentError('argument -t/--icmp-type-code: not compatible '
                                'with protocol "{0}"'.format(protocol))
        if not port_range:
            raise ArgumentError('argument -p/--port-range is required '
                                'for protocol "{0}"'.format(protocol))
        if ':' in port_range:
            # Be extra helpful in the event of this common typo
            raise ArgumentError('argument -p/--port-range: multi-port '
                                'range must be separated by "-", not ":"')
        from_port, to_port = _parse_port_range(port_range, protocol)
        if from_port < -1 or to_port < -1:
            raise ArgumentError('argument -p/--port-range: port number(s) '
                                'must be at least -1')
        if from_port == -1:
            from_port = 1
        if to_port == -1:
            to_port = 65535
    # We allow other protocols through without parsing port numbers at all.
    return from_port, to_port


def _parse_port_range(port_range, protocol):
    # Try for an integer
    try:
        return (int(port_range), int(port_range))
    except ValueError:
        pass
    # Try for an integer range
    if port_range.count('-') == 1:
        ports = port_range.split('-')
        try:
            return (int(ports[0]), int(ports[1]))
        except ValueError:
            pass
    # Try for a service name
    if isinstance(protocol, six.string_types):
        try:
            # This is going to fail if protocol is a number.
            port = socket.getservbyname(port_range, protocol)
            return (port, port)
        except socket.error:
            pass
    # That's all, folks!
    raise ArgumentError("argument -p/--port-range: '{0}' is neither a port "
                        "number, range of port numbers, nor a recognized "
                        "service name".format(port_range))
