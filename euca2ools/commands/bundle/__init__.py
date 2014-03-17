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

import argparse
import os.path
from euca2ools.commands import Euca2ools
from euca2ools.commands.argtypes import (delimited_list, filesize,
                                         manifest_block_device_mappings)
from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import (FileTransferProgressBarMixin,
                                   RegionConfigurableMixin)


class BundleCreator(BaseCommand, FileTransferProgressBarMixin,
                    RegionConfigurableMixin):
    SUITE = Euca2ools
    REGION_ENVVAR = 'EUCA_REGION'
    ARGS = [Arg('-r', '--arch', choices=('i386', 'x86_64', 'armhf'),
                required=True,
                help="the image's processor architecture (required)"),
            Arg('-c', '--cert', metavar='FILE',
                help='file containing your X.509 certificate.'),
            Arg('-k', '--privatekey', metavar='FILE', help='''file containing
                the private key to sign the bundle's manifest with.  This
                private key will also be required to unbundle the image in
                the future.'''),
            Arg('-u', '--user', metavar='ACCOUNT', help='your account ID'),
            Arg('--ec2cert', metavar='FILE', help='''file containing the
                cloud's X.509 certificate'''),
            Arg('--kernel', metavar='IMAGE', help='''ID of the kernel image to
                associate with the machine bundle'''),
            Arg('--ramdisk', metavar='IMAGE', help='''ID of the ramdisk image
                to associate with the machine bundle'''),
            Arg('-B', '--block-device-mappings',
                metavar='VIRTUAL1=DEVICE1,VIRTUAL2=DEVICE2,...',
                type=manifest_block_device_mappings,
                help='''default block device mapping scheme with which to
                launch instances of this machine image'''),
            Arg('-d', '--destination', metavar='DIR', help='''location to
                place the bundle's files (default:  dir named by TMPDIR, TEMP,
                or TMP environment variables, or otherwise /var/tmp)'''),
            Arg('--part-size', type=filesize, default=10485760,  # 10m
                help=argparse.SUPPRESS),
            Arg('--productcodes', metavar='CODE1,CODE2,...',
                type=delimited_list(','), default=[],
                help='comma-separated list of product codes'),
            Arg('--batch', action='store_true', help=argparse.SUPPRESS)]

    # noinspection PyExceptionInherit
    def configure(self):
        BaseCommand.configure(self)

        self.update_config_view()

        # Get creds
        add_bundle_creds(self.args, self.config)
        if not self.args.get('cert'):
            raise ArgumentError(
                'missing certificate; please supply one with -c')
        self.log.debug('certificate: %s', self.args['cert'])
        if not self.args.get('privatekey'):
            raise ArgumentError(
                'missing private key; please supply one with -k')
        self.log.debug('private key: %s', self.args['privatekey'])
        if not self.args.get('ec2cert'):
            raise ArgumentError(
                'missing cloud certificate; please supply one with --ec2cert')
        self.log.debug('cloud certificate: %s', self.args['ec2cert'])
        if not self.args.get('user'):
            raise ArgumentError(
                'missing account ID; please supply one with --user')
        self.log.debug('account ID: %s', self.args['user'])

        if (self.args.get('destination') and
            os.path.exists(self.args['destination']) and not
            os.path.isdir(self.args['destination'])):
            raise ArgumentError("argument -d/--destination: '{0}' is not a "
                                "directory".format(self.args['destination']))


# noinspection PyExceptionInherit
def add_bundle_creds(args, config):
    # User's X.509 certificate (user-level in config)
    if not args.get('cert'):
        config_cert = config.get_user_option('certificate')
        if 'EC2_CERT' in os.environ:
            args['cert'] = os.getenv('EC2_CERT')
        elif 'EUCA_CERT' in os.environ:  # used by the NC
            args['cert'] = os.getenv('EUCA_CERT')
        elif config_cert:
            args['cert'] = config_cert
    if args.get('cert'):
        args['cert'] = os.path.expanduser(os.path.expandvars(args['cert']))
        if not os.path.exists(args['cert']):
            raise ArgumentError("certificate file '{0}' does not exist"
                                .format(args['cert']))
        if not os.path.isfile(args['cert']):
            raise ArgumentError("certificate file '{0}' is not a file"
                                .format(args['cert']))

    # User's private key (user-level in config)
    if not args.get('privatekey'):
        config_privatekey = config.get_user_option('private-key')
        if 'EC2_PRIVATE_KEY' in os.environ:
            args['privatekey'] = os.getenv('EC2_PRIVATE_KEY')
        if 'EUCA_PRIVATE_KEY' in os.environ:  # used by the NC
            args['privatekey'] = os.getenv('EUCA_PRIVATE_KEY')
        elif config_privatekey:
            args['privatekey'] = config_privatekey
    if args.get('privatekey'):
        args['privatekey'] = os.path.expanduser(os.path.expandvars(
            args['privatekey']))
        if not os.path.exists(args['privatekey']):
            raise ArgumentError("private key file '{0}' does not exist"
                                .format(args['privatekey']))
        if not os.path.isfile(args['privatekey']):
            raise ArgumentError("private key file '{0}' is not a file"
                                .format(args['privatekey']))

    # Cloud's X.509 cert (region-level in config)
    if not args.get('ec2cert'):
        config_privatekey = config.get_region_option('certificate')
        if 'EUCALYPTUS_CERT' in os.environ:
            # This has no EC2 equivalent since they just bundle their cert.
            args['ec2cert'] = os.getenv('EUCALYPTUS_CERT')
        elif config_privatekey:
            args['ec2cert'] = config_privatekey
    if args.get('ec2cert'):
        args['ec2cert'] = os.path.expanduser(os.path.expandvars(
            args['ec2cert']))
        if not os.path.exists(args['ec2cert']):
            raise ArgumentError("cloud certificate file '{0}' does not exist"
                                .format(args['ec2cert']))
        if not os.path.isfile(args['ec2cert']):
            raise ArgumentError("cloud certificate file '{0}' is not a file"
                                .format(args['ec2cert']))

    # User's account ID (user-level)
    if not args.get('user'):
        config_account_id = config.get_user_option('account-id')
        if 'EC2_USER_ID' in os.environ:
            args['user'] = os.getenv('EC2_USER_ID')
        elif config_account_id:
            args['user'] = config_account_id
