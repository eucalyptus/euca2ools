# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2013, Eucalyptus Systems, Inc.
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
#

from euca2ools.utils import execute, check_command, sanitize_path
from euca2ools.utils import mkdtemp_for_large_files as mkdtemp
import os
import sys
import platform
import shutil


NO_EXCLUDE_ENVAR = 'EUCA_BUNDLE_VOL_EMPTY_EXCLUDES'
BLKID_TAGS = ('LABEL', 'TYPE', 'UUID')
ALLOWED_FS_TYPES = ('ext2', 'ext3', 'xfs', 'jfs', 'reiserfs')
EXCLUDED_DIRS = ('/dev', '/media', '/mnt', '/proc',
                 '/sys', '/cdrom', '/tmp')
SYSTEM_DIRS = ('proc', 'tmp', 'dev', 'mnt', 'sys')
DEVICE_NODES = (('/dev/console', 'c', '5', '1'),
                ('/dev/full', 'c', '1', '7'),
                ('/dev/null', 'c', '1', '3'),
                ('/dev/zero', 'c', '1', '5'),
                ('/dev/tty', 'c', '5', '0'),
                ('/dev/tty0', 'c', '4', '0'),
                ('/dev/tty1', 'c', '4', '1'),
                ('/dev/tty2', 'c', '4', '2'),
                ('/dev/tty3', 'c', '4', '3'),
                ('/dev/tty4', 'c', '4', '4'),
                ('/dev/tty5', 'c', '4', '5'),
                ('/dev/xvc0', 'c', '204', '191'))
FSTAB_BODY_TEMPLATE = dict(
    i386="""/dev/sda1\t/\text3\tdefaults 1 1
/dev/sdb\t/mnt\text3\tdefaults 0 0
none\t/dev/pts\tdevpts\tgid=5,mode=620 0 0
none\t/proc\tproc\tdefaults 0 0
none\t/sys\tsysfs\tdefaults 0 0""",
    x86_64="""/dev/sda1\t/\text3\tdefaults,errors=remount-ro 0 0
/dev/sda2\t/mnt\text3\tdefaults\t0 0
/dev/sda3\tswap\tswap\tdefaults\t0 0
proc\t/proc\tproc\tdefaults\t0 0
devpts\t/dev/pts\tdevpts\tgid=5,mode=620 0 0""",
    )
FSTAB_HEADER_TEMPLATE = """#
#
# /etc/fstab
#
# Created by euca-bundle-vol on {0}
#
#"""
FSTAB_TIME_FORMAT = "%a %b %d %H:%M:%S %Y"
DEFAULT_PATTERN_EXCLUDES = [
    '*/#*#',
    '*/.#*',
    '*.sw',
    '*.swo',
    '*.swp',
    '*~',
    '*.pem',
    '*.priv',
    '*id_rsa*',
    '*id_dsa*',
    '*.gpg',
    '*.jks',
    '*/.ssh/authorized_keys',
    '*/.bash_history',
]
DEFAULT_FS_EXCLUDES = [
    '/dev',
    '/media',
    '/mnt',
    '/proc',
    '/sys',
]


class VolumeSync(object):
    def __init__(self, volume, image):
        self.mount = mkdtemp()
        self.excludes = []
        self.filter = False
        self.fstab = None
        self.generate_fstab = False
        self.image = image
        self.includes = []
        self.volume = volume
        self.bundle_all_dirs = False

    def run(self):
        #
        # This is where ALL the magic happens!
        #
        self._sync_files()
        self._populate_system_dirs()
        self._populate_device_nodes()
        self._populate_tmpfs_mounts()

        #
        # If an fstab file was specified we will replace the current
        # fstab on the created image with the file supplied. If the
        # user has told us to generate a new fstab file, then we will
        # create a new one based on the architecture of the target
        # system. If neither are specified then we do nothing here and
        # the user keeps their fstab from the original volume.
        #
        if self.fstab:
            with open(fstab, 'r') as fp:
                self._install_fstab(fp.read())
        elif self.generate_fstab:
            self._install_generated_fstab()

    def exclude(self, exclude):
        if exclude:
            if isinstance(exclude, list):
                self.excludes.extend(exclude)
            else:
                self.excludes.append(exclude)

    def include(self, include):
        if include:
            if isinstance(include, list):
                self.includes.extend(include)
            else:
                self.includes.append(include)

    def bundle_all_dirs(self):
        self.bundle_all_dirs = True

    def filter_files(self):
        self.filter = True

    def install_fstab_from_file(self, fstab):
        if not os.path.exists(fstab):
            raise ArgumentError(
                'fstab file '{0}' does not exist.'.format(fstab))
        self.fstab = fstab

    def generate_fstab(self):
        self.generate_fstab = True

    def _update_exclusions(self):
        #
        # Here we update the following sync exclusions:
        #
        # 1. Exclude our disk image we are syncing to.
        # 2. Exclude our mount point for our image.
        # 3. Exclude filesystems that are not allowed.
        # 4. Exclude special system directories.
        # 5. Exclude file patterns for privacy.
        # 6. Exclude problematic udev rules.
        #
        if self.image.find(self.volume) == 0:
            self.exclude(os.path.dirname(self.image))
        if self.mount(self.volume) == 0:
            self.exclude(self.mount)
        if not self.bundle_all_dirs:
            self._add_mtab_exclusions()
        self.excludes.extend(EXCLUDED_DIRS)
        if self.filter:
            self.excludes.extend(DEFAULT_PATTERN_EXCLUDES)
        if os.environ.get(NO_EXCLUDE_ENVAR, "0") == "0":
            self.excludes.extend(
                ['/etc/udev/rules.d/70-persistent-net.rules',
                 '/etc/udev/rules.d/z25_persistent-net.rules'])

    def _add_mtab_exclusions(self):
        with open('/etc/mtab', 'r') as mtab:
            for line in mtab.readlines():
                (mount, type) = line.split()[1:3]
                #
                # If we find that a mount in our volume's mtab file is
                # and shares a parent directory with the volume we will
                # check if the filesystem for the mount is not allowed
                # (e.g., NFS) and we will exclude it. This will not happen
                # if you have chosen the 'all' option.
                #
                if mount.find(self.volume) == 0 and type \
                    not in ALLOWED_FS_TYPES:
                    self.excludes.append(mount)

    def _populate_tmpfs_mounts(self):
        with open('/etc/mtab', 'r') as mtab:
            for line in mtab.readlines():
                (mount, type) = line.split()[1:3]
                if type == 'tmpfs':
                    fullpath = os.path.join(self.mount, mount[1:])
                    if not os.path.exists(fullpath):
                        os.makedirs(fullpath)

    def _populate_device_nodes(self):
        template = 'mknod {0} {1} {2} {3}'
        for node in DEVICE_NODES:
            cmd = template.format(node[0], *node[1:])
            execute(cmd)

    def _populate_system_dirs(self):
        for sysdir in SYSTEM_DIRS:
            fullpath = os.path.join(self.mount, sysdir)
            if not os.path.exists(fullpath):
                os.makedirs(fullpath)
                if sysdir == 'tmp':
                    os.chmod(fullpath, 01777)

    def _install_generated_fstab(self):
        self._install_fstab(_generate_fstab_content())

    def _install_fstab(self, content):
        curr_fstab = os.path.join(self.mount, 'etc', 'fstab')
        if os.path.exists(curr_fstab):
            shutil.copyfile(curr_fstab, curr_fstab + '.old')
            os.remove(curr_fstab)
        with open(os.path.join(mount, 'etc', 'fstab'), 'wb') as fp:
            fp.write(content)

    def _sync_files(self):
        check_command('rsync')
        cmd = ['rsync', '-aXS']
        self._update_exclusions()
        for exclude in self.excludes:
            cmd.extend(['--exclude', exclude])
        for include in self.includes:
            cmd.extend(['--include', include])
        cmd.extend([os.path.join(self.volume, '*'), self.dest])
        (out, _, retval) = execute(cmd)

        #
        # rsync return code 23: Partial transfer due to error
        # rsync return code 24: Partial transfer due to vanished source files
        #
        if retval in (23, 24):
            print >> sys.stderr, 'Warning: rsync reports files partially copied:'
            print >> sys.stderr, out
        else:
            print >> sys.stderr, 'Error: rsync failed with return code {0}'.format(retval)
            raise CopyError

    def _sync_disks(self):
        execute('sync')

    def mount(self):
        self._sync_disks()
        if not os.path.exists(self.mount):
            os.makedirs(self.mount)
        check_command('mount')
        cmd = ['mount', '-o', 'loop', self.image, self.mount]
        execute(cmd)

    def unmount(self):
        self._sync_disks()
        utils.check_command('umount')
        cmd = ['umount', '-d', self.dest]
        execute(cmd)
        if os.path.exists(self.mount):
            os.remove(self.mount)

    def __enter__(self):
        self.mount()
        return self

    def __exit__(self, type, value, traceback):
        self.unmount()


class ImageCreator(object):
    def __init__(self, **kwargs):
        self.volume = sanitize_path(kwargs.get('volume', '/'))
        self.fstab = kwargs.get('fstab')
        self.generate_fstab = kwargs.get('generate_fstab', False)
        self.excludes = kwargs.get('exclude', [])
        self.includes = kwargs.get('include', [])
        self.bundle_all_dirs = kwargs.get('bundle_all_dirs', False)
        self.size = kwargs.get('size')
        self.prefix = kwargs.get('prefix')
        self.image = os.path.join(mkdtemp(), '{0}.img'.format(self.prefix))
        self.fs = {}

    def run(self):
        #
        # Prepare a disk image
        # 
        self._create_raw_diskimage()
        self._populate_filesystem_info()
        self._make_filesystem(**self.fs)
        #
        # Inside the VolumeSync context we will mount our image
        # as a loop device. If for any reason a failure occurs
        # the device will automatically be unmounted and cleaned up.
        #
        with VolumeSync(self.volume, self.image) as volsync:
            if self.fstab:
                volsync.install_fstab_from_file(self.fstab)
            elif self.generate_fstab:
                volsync.generate_fstab()
            if self.filter:
                volsync.filter_files()
            volsync.exclude(self.excludes)
            volsync.include(self.includes)
            volsync.run()

        return self.image

    def _create_raw_diskimage(self):
        template = 'dd if=/dev/zero of={0} count=1 bs=1M seek {1}'
        cmd = template.format(self.image, self.args.get('size') - 1)
        execute(cmd)

    def _populate_filesystem_info(self):
        #
        # Create a temporary device node for the volume we're going
        # to copy. We'll use it to get information about the filesystem.
        #
        st_dev = os.stat(self.volume).st_dev
        devid = os.makedev(os.major(st_dev), os.minor(st_dev))
        directory = mkdtemp()
        devnode = os.path.join(directory, 'rootdev')
        os.mknod(devnode, 0400 | stat.S_IFBLK, devid)
        template = 'blkid -s {0} -ovalue {1}'
        try:
            for tag in BLKID_TAGS:
                cmd = template.format(tag, devnode)
                try:
                    (out, _, _) = execute(cmd)
                    self.fs[tag.lower()] = out.rstrip()
                except CommandFailed:
                    pass
        finally:
            os.remove(devnode)
            os.rmdir(directory)
   
    def _make_filesystem(self, type='ext3', uuid=None, label=None):
        mkfs_cmd = 'mkfs.{0}'.format(type)
        tunefs = None

        if type.startswith('ext'):
            mkfs = [mkfs_cmd, '-F', self.image]
            if uuid:
                tunefs = ['tune2fs', '-U', uuid, self.image]
        elif type == 'xfs':
            mkfs = [mkfs_cmd, self.image]
            tunefs = ['xfs_admin', '-U', uuid, self.image]
        elif type == 'btrfs':
            mkfs = [mkfs_cmd, self.image]
            if uuid:
                raise UnsupportedException("btrfs with uuid not supported")
        else:
            raise UnsupportedException("unsupported fs {0}".format(type))

        if label:
            mkfs.extend(['-L', label])
        utils.check_command(mkfs)
        execute(mkfs)
        if tunefs:
            utils.check_command(tunefs)
            execute(tunefs)


def _generate_fstab_content(arch=platform.machine()):
    if arch in FSTAB_BODY_TEMPLATE:
        return "\n".join(FSTAB_HEADER_TEMPLATE.format(
                time.strftime(FSTAB_TIME_FORMAT)),
                         FSTAB_BODY_TEMPLATE.get(arch))
    else:
        raise UnsupportedException(
            "platform architecture {0} not supported".format(arch))
