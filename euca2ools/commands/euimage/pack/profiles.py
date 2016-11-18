# Copyright (c) 2014-2016 Hewlett Packard Enterprise Development LP
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

import datetime
import six

from euca2ools.commands.bundle.bundleanduploadimage import BundleAndUploadImage
from euca2ools.commands.ec2.createtags import CreateTags
from euca2ools.commands.ec2.registerimage import RegisterImage
from euca2ools.util import check_dict_whitelist, transform_dict


def build_image_profile(profile_dict, arch):
    """
    This is a factory method that takes a dict with image profile
    information and returns a profile object.  While it currently always
    returns instance-store images, it is meant to handle multiple types
    in the future.
    """
    if 'bundle' in profile_dict:
        return InstanceStoreImageProfile(profile_dict, arch)


class InstanceStoreImageProfile(object):
    def __init__(self, profile_dict, arch):
        check_dict_whitelist(profile_dict, 'profile',
                             ['bundle', 'provides', 'register', 'tag'])
        self.bundle_args = {}
        self.register_args = {}
        self.tag_args = {}

        bundle_args = profile_dict.get('bundle') or {}
        bundle_args.setdefault('arch', arch)
        self.__load_bundle_args(bundle_args)
        register_args = profile_dict.get('register') or {}
        register_args.setdefault('arch', arch)
        self.__load_register_args(register_args)
        self.__load_tag_args(profile_dict.get('tag') or {})

    def __load_bundle_args(self, args):
        check_dict_whitelist(args, 'bundle', ['arch'])
        self.bundle_args.update(args)
        if not self.bundle_args.get('arch'):
            raise ValueError('register: arch is required')

    def __load_register_args(self, args):
        check_dict_whitelist(args, 'register',
                             ['arch', 'block-device-mappings', 'description',
                              'platform', 'virtualization-type'])
        self.register_args.update(transform_dict(
            args,
            {'arch': 'Architecture',
             'description': 'Description',
             'platform': 'Platform',
             'virtualization-type': 'VirtualizationType'}))
        if not self.register_args.get('Architecture'):
            raise ValueError('register: arch is required')
        mappings = self.register_args.pop('block-device-mappings', None) or {}
        if not isinstance(mappings, dict):
            raise ValueError('register: block-device-mappings must be an '
                             'associative array')
        for device, mapping_info in mappings.items():
            mapping = {'DeviceName': device}
            if mapping_info == 'none':
                mapping['NoDevice'] = 'true'
            elif (isinstance(mapping_info, six.string_types) and
                  mapping_info.startswith('ephemeral')):
                mapping['VirtualName'] = mapping_info
            elif isinstance(mapping_info, dict):
                mapping['Ebs'] = transform_dict(
                    mapping_info,
                    {'snapshot-id': 'SnapshotId',
                     'volume-size': 'VolumeSize',
                     'delete-on-termination': 'DeleteOnTermination'})
                if (not mapping['Ebs'].get('SnapshotId') and
                        not mapping['Ebs'].get('VolumeSize')):
                    raise ValueError('register: block device mapping {0} '
                                     'requires a volume-size')
            else:
                raise ValueError('register: unreadable block device mapping')

    def __load_tag_args(self, args):
        check_dict_whitelist(args, 'tag')
        tags = []
        for key, val in args.items():
            tags.append({'Key': key, 'Value': val})
        if tags:
            self.tag_args.setdefault('Tag', [])
            self.tag_args['Tag'].extend(tags)

    def install(self, image_md, services, image_fileobj, image_size, args,
                tags=None):
        # If you're curious why this uses a generic "args" dict, see
        # ImageMetadata.install_profile's commentary.
        bundle_args = dict(self.bundle_args)
        for argname in ('privatekey', 'cert', 'ec2cert', 'user', 'bucket',
                        'location', 'kernel', 'ramdisk'):
            if args.get(argname):
                bundle_args[argname] = args[argname]
        req = BundleAndUploadImage(
            service=services['s3']['service'],
            config=services['s3']['service'].config,
            loglevel=services['s3']['service'].log.level,
            auth=services['s3']['auth'], image=image_fileobj,
            prefix=image_md.get_nvra(),
            image_type='machine',  # We only support machine images for now
            image_size=image_size, show_progress=args.get('show_progress'),
            max_pending_parts=2, part_size=10485760, **bundle_args)
        try:
            bundle_info = req.main()
        except KeyError as err:
            raise ValueError('{0} is required'.format(err.args[0]))

        register_args = dict(self.register_args)
        if args.get('kernel'):
            register_args['KernelId'] = args['kernel']
        if args.get('ramdisk'):
            register_args['RamdiskId'] = args['ramdisk']
        if not register_args.get('Description'):
            register_args['Description'] = image_md.description
        req = RegisterImage(
            service=services['ec2']['service'],
            config=services['ec2']['service'].config,
            loglevel=services['ec2']['service'].log.level,
            auth=services['ec2']['auth'],
            ImageLocation=bundle_info['manifests'][0]['key'],
            Name='{0}-{1}'.format(
                image_md.get_nvra(),
                datetime.datetime.utcnow().strftime('%F-%H-%m-%s')),
            **register_args)
        register_response = req.main()
        image_id = register_response['imageId']

        tag_args = dict(self.tag_args)
        tag_args['ResourceId'] = [image_id]
        tag_args.setdefault('Tag', [])
        if tags:
            for key, val in tags.items():
                tag_args['Tag'].append({'Key': key, 'Value': val})
        req = CreateTags(
            service=services['ec2']['service'],
            config=services['ec2']['service'].config,
            loglevel=services['ec2']['service'].log.level,
            auth=services['ec2']['auth'], **tag_args)
        req.main()

        return image_id
