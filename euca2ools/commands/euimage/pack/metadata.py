# (C) Copyright 2014 Eucalyptus Systems, Inc.
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

import yaml

from euca2ools.commands.euimage.pack.profiles import build_image_profile
from euca2ools.util import check_dict_whitelist


class ImagePackMetadata(object):
    def __init__(self):
        self.image_sha256sum = None
        self.image_size = None
        self.image_md_sha256sum = None
        self.version = 1  # Bump this with each incompatible change

    @classmethod
    def from_fileobj(cls, fileobj):
        new_md = cls()
        metadata = yaml.safe_load(fileobj)
        check_dict_whitelist(metadata, 'pack', ['image', 'image_metadata',
                                                'version'])
        if metadata.get('version'):
            # This is the version of the pack metadata, not the image.
            # If we make backwards-incompatible changes this allows us
            # to tell what to expect so we can continue to handle packs
            # that precede those changes.
            #
            # Because there is only one metadata version right now this
            # method is rather dumb -- it accepts only version 1.
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
        return new_md

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
        self.description = None
        self.profiles = {}

    @classmethod
    def from_fileobj(cls, fileobj):
        new_md = cls()
        metadata = yaml.safe_load(fileobj)
        check_dict_whitelist(metadata, 'image',
                             ['name', 'version', 'release', 'arch',
                              'description', 'profiles'])
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
            raise ValueError('image "{0}": arch is missing or empty'
                             .format(new_md.name))
        new_md.arch = metadata['arch']
        if not metadata.get('description'):
            raise ValueError('image "{0}": description is missing or empty'
                             .format(new_md.name))
        new_md.description = metadata['description'].rstrip()
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

    def install_profile(self, profile_name, services, image_fileobj,
                        image_size, args):
        # Since different profiles can require different args to install
        # correctly, we can't easily pick out the correct ones ahead
        # of time.  For simplicity's sake, we just pass everything and
        # let the profile grab what it needs.  Validation is the job of
        # the profile, which will probably simply delegate that work to
        # the commands it runs.
        euimage_tags = {'euimage:name': self.name,
                        'euimage:version': self.version,
                        'euimage:release': self.release,
                        'euimage:profile': profile_name}
        if self.epoch:
            euimage_tags['euimage:epoch'] = self.epoch
        if profile_name not in self.profiles:
            raise ValueError('no such profile: "{0}"'.format(profile_name))
        return self.profiles[profile_name].install(
            self, services, image_fileobj, image_size, args, tags=euimage_tags)

    def get_nvra(self):
        return '{0}-{1}-{2}.{3}'.format(self.name, self.version, self.release,
                                        self.arch)
