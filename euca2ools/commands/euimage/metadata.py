# (C) Copyright 2014 Hewlett-Packard Development Company, L.P.
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


import six
import yaml


class ImagePackMetadata(object):
    def __init__(self):
        self.image_sha256sum = None
        self.image_size = None
        self.image_md_sha256sum = None
        self.version = 1

    @classmethod
    def from_fileobj(cls, fileobj):
        new_md = cls()
        metadata = yaml.safe_load(fileobj)
        _check_dict_whitelist(metadata, 'pack', ['image', 'image_metadata',
                                                 'version'])
        if metadata.get('version'):
            if int(metadata['version']) != 1:
                raise ValueError('pack has metadata version {0}; expected 1'
                                 .format(metadata['version']))
        image_info = metadata.get('image') or {}
        if not image_info.get('sha256sum'):
            raise ValueError('pack: image.sha256sum is missing or empty')
        new_md.image_sha256sum = image_info['sha256sum']
        if not image_info.get('size'):
            raise ValueError('pack: image.size is missing or zero')
        new_md.image_size = int(image_info['size'])
        image_md_info = metadata.get('image_metadata') or {}
        if not image_md_info.get('sha256sum'):
            raise ValueError(
                'pack: image_metadata.sha256sum is missing or empty')
        new_md.image_md_sha256sum = image_md_info['sha256sum']

    @classmethod
    def from_file(cls, filename):
        with open(filename) as fileobj:
            return cls.from_fileobj(fileobj)

    def dump_to_fileobj(self, fileobj):
        yaml.safe_dump(self.__serialize_as_dict(), fileobj,
                       default_flow_style=False)

    def dump_to_file(self, filename):
        with open(filename, 'w') as fileobj:
            self.dump_to_fileobj(fileobj)

    def __serialize_as_dict(self):
        return {'image': {'sha256sum': self.image_sha256sum,
                          'size': self.image_size},
                'image_metadata': {'sha256sum': self.image_md_sha256sum},
                                   'version': self.version}


class ImageMetadata(object):
    def __init__(self):
        self.name = None
        self.version = None
        self.release = None
        self.epoch = 0
        self.arch = None
        self.profiles = {}

    @classmethod
    def from_fileobj(cls, fileobj):
        new_md = cls()
        metadata = yaml.safe_load(fileobj)
        _check_dict_whitelist(metadata, 'image',
                              ['name', 'version', 'release', 'arch',
                               'profiles'])
        if not metadata.get('name'):
            raise ValueError('name is missing or empty')
        new_md.name = metadata['name']
        if not metadata.get('version'):
            raise ValueError('image "{0}": version is missing or empty'
                             .format(new_md.name))
        new_md.version = metadata['version']
        if not metadata.get('release'):
            raise ValueError('image "{0}": release is missing or empty'
                             .format(new_md.name))
        new_md.release = metadata['release']
        if metadata.get('epoch'):
            try:
                new_md.epoch = int(metadata['epoch'])
            except ValueError:
                raise ValueError('image "{0}": epoch must be an integer'
                                 .format(new_md.name))
            if new_md.epoch < 0:
                raise ValueError('image "{0}": epoch must not be negative'
                                 .format(new_md.name))
        if not metadata.get('arch'):
            raise ValueError('image "{0}": arch is missing or empty')
        new_md.arch = metadata['arch']
        profiles = metadata.get('profiles')
        if not profiles:
            raise ValueError('image "{0}" must have at least one profile '
                             '(use "default" for a single-profile image)'
                             .format(new_md.name))
        if not isinstance(profiles, dict):
            raise ValueError('image "{0}": profiles must be an associative '
                             'array'.format(new_md.name))
        for profile_name, profile_info in profiles.iteritems():
            new_md.profiles[profile_name] = build_image_profile(profile_info,
                                                                new_md.arch)
        return new_md

    @classmethod
    def from_file(cls, filename):
        with open(filename) as fileobj:
            return cls.from_fileobj(fileobj)


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
        _check_dict_whitelist(profile_dict, 'profile',
                              ['bundle', 'register', 'tag'])
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

    def execute(self):
        ## TODO
        raise NotImplementedError()

    def __load_bundle_args(self, args):
        _check_dict_whitelist(args, 'bundle', ['arch'])
        self.bundle_args.update(args)
        if not self.bundle_args.get('arch'):
            raise ValueError('register: arch is required')

    def __load_register_args(self, args):
        ## TODO:  copy the image-level description if none is supplied here
        _check_dict_whitelist(args, 'register',
                              ['arch', 'block-device-mappings', 'description',
                               'platform', 'virtualization-type'])
        self.register_args.update(_transform_dict(
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
        for device, mapping_info in mappings.iteritems():
            mapping = {'DeviceName': device}
            if mapping_info == 'none':
                mapping['NoDevice'] = 'true'
            elif (isinstance(mapping_info, six.string_types) and
                  mapping_info.startswith('ephemeral')):
                mapping['VirtualName'] = mapping_info
            elif isinstance(mapping_info, dict):
                mapping['Ebs'] = _transform_dict(
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
        _check_dict_whitelist(args, 'tag')
        self.tag_args.update(args)


def _check_dict_whitelist(dict_, err_context, whitelist=None):
    if not isinstance(dict_, dict):
        raise ValueError('{0} must be an associative array'
                         .format(err_context))
    if whitelist:
        differences = set(dict_.keys()) - set(whitelist)
        if differences:
            raise ValueError('unrecognized {0} argument(s): {1}'
                             .format(err_context, ', '.join(differences)))


def _transform_dict(dict_, transform_dict):
    transformed = {}
    for key, val in dict_.iteritems():
        if key in transform_dict:
            transformed[transform_dict[key]] = val
        else:
            transformed[key] = val
    return transformed
