# Copyright 2009-2013 Eucalyptus Systems, Inc.
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

from euca2ools.util import sanitize_path
from euca2ools.util import mkdtemp_for_large_files as mkdtemp
import glob
import os
import sys
import platform
import shutil
import stat
import subprocess
import time


NO_EXCLUDE_ENVAR = 'EUCA_BUNDLE_VOL_EMPTY_EXCLUDES'
BLKID_TAGS = {'LABEL': 'label',
              'TYPE': 'fstype',
              'UUID': 'uuid'}
ALLOWED_FS_TYPES = ('ext2', 'ext3', 'ext4', 'xfs', 'jfs', 'reiserfs')
EXCLUDED_DIRS = ('/dev', '/media', '/mnt', '/proc',
                 '/sys', '/cdrom', '/tmp')
SYSTEM_DIRS = ('proc', 'tmp', 'dev', 'mnt', 'sys')
DEVICE_NODES = {'dev/console': ['c', '5', '1'],
                'dev/full': ['c', '1', '7'],
                'dev/null': ['c', '1', '3'],
                'dev/zero': ['c', '1', '5'],
                'dev/tty': ['c', '5', '0'],
                'dev/tty0': ['c', '4', '0'],
                'dev/tty1': ['c', '4', '1'],
                'dev/tty2': ['c', '4', '2'],
                'dev/tty3': ['c', '4', '3'],
                'dev/tty4': ['c', '4', '4'],
                'dev/tty5': ['c', '4', '5'],
                'dev/xvc0': ['c', '204', '191']}
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
devpts\t/dev/pts\tdevpts\tgid=5,mode=620 0 0""")
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
#
# We're using /etc/mtab since this is what the AWS tools do. Other tools like
# df also read the /etc/mtab file for mounts. Even though /proc/mounts is
# more up to date, we'll stick with this unless there's a good reason to
# change it.
#
MOUNTS_FILE = '/etc/mtab'


class VolumeSync(object):
    def __init__(self, volume, image, log=None):
        self.log = log
        self.mpoint = mkdtemp(prefix='vol-')
        self.excludes = []
        self.filter = False
        self.fstab = None
        self.generate_fstab_file = False
        self.image = image
        self.includes = []
        self.volume = volume
        self.bundle_all_dirs = False

    def run(self):
        """
        This is where ALL the magic happens!
        """
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
            with open(self.fstab, 'r') as fstab_file:
                self._install_fstab(fstab_file.read())
        elif self.generate_fstab_file:
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

    def bundle_all(self):
        self.bundle_all_dirs = True

    def filter_files(self):
        self.filter = True

    def install_fstab_from_file(self, fstab):
        if not os.path.exists(fstab):
            raise ValueError(
                "fstab file '{0}' does not exist.".format(fstab))
        self.fstab = fstab

    def generate_fstab(self):
        self.generate_fstab_file = True

    def _update_exclusions(self):
        """
        Here we update the following sync exclusions:

        1. Exclude our disk image we are syncing to.
        2. Exclude our mount point for our image.
        3. Exclude filesystems that are not allowed.
        4. Exclude special system directories.
        5. Exclude file patterns for privacy.
        6. Exclude problematic udev rules.
        """

        if self.image.find(self.volume) == 0:
            self.exclude(os.path.dirname(self.image))
        if self.mpoint.find(self.volume) == 0:
            self.exclude(self.mpoint)
        if not self.bundle_all_dirs:
            self._add_mounts_exclusions()
        self.excludes.extend(EXCLUDED_DIRS)
        if self.filter:
            self.excludes.extend(DEFAULT_PATTERN_EXCLUDES)
        if os.environ.get(NO_EXCLUDE_ENVAR, "0") == "0":
            self.excludes.extend(
                ['/etc/udev/rules.d/70-persistent-net.rules',
                 '/etc/udev/rules.d/z25_persistent-net.rules'])

    def _add_mounts_exclusions(self):
        """Exclude locations from the volume rsync based on whether we are
        allowed to sync the type of filesystem. If you have chosen to bundle
        all using '--all' then this will not get called.
        """
        with open(MOUNTS_FILE, 'r') as mounts:
            for line in mounts.readlines():
                (mount, fstype) = line.split()[1:3]
                #
                # If we find that a mount in our volume's mtab file is
                # and shares a parent directory with the volume we will
                # check if the filesystem for the mount is not allowed
                # (e.g., NFS) and we will exclude it. This will not happen
                # if you have chosen the 'all' option.
                #
                if (mount.find(self.volume) == 0 and
                    fstype not in ALLOWED_FS_TYPES):

                    self.excludes.append(mount)

    def _populate_tmpfs_mounts(self):
        """Find all tmpfs mounts on our volume and make sure that they are
        created on the image.
        """
        with open(MOUNTS_FILE, 'r') as mounts:
            for line in mounts.readlines():
                (mount, fstype) = line.split()[1:3]
                if fstype == 'tmpfs':
                    fullpath = os.path.join(self.mpoint, mount[1:])
                    if not os.path.exists(fullpath):
                        os.makedirs(fullpath)

    def _populate_device_nodes(self):
        """Populate the /dev directory in our image with common device nodes."""
        for node, args in DEVICE_NODES.iteritems():
            subprocess.check_call(['mknod',
                                   os.path.join(self.mpoint, node)] + args)

    def _populate_system_dirs(self):
        """Populate our image with common system directories."""
        for sysdir in SYSTEM_DIRS:
            fullpath = os.path.join(self.mpoint, sysdir)
            if not os.path.exists(fullpath):
                os.makedirs(fullpath)
                if sysdir == 'tmp':
                    os.chmod(fullpath, 01777)

    def _install_generated_fstab(self):
        self._install_fstab(_generate_fstab_content())

    def _install_fstab(self, content):
        fstab_path = os.path.join(self.mpoint, 'etc', 'fstab')
        if os.path.exists(fstab_path):
            shutil.copyfile(fstab_path, fstab_path + '.old')
            os.remove(fstab_path)
        with open(fstab_path, 'wb') as fstab:
            fstab.write(content)

    def _sync_files(self):
        cmd = ['rsync', '-aXS']
        self._update_exclusions()
        for exclude in self.excludes:
            cmd.extend(['--exclude', exclude])
        for include in self.includes:
            cmd.extend(['--include', include])
        cmd.extend(glob.glob(os.path.join(self.volume, '*')))
        cmd.append(self.mpoint + os.path.sep)

        try:
            if self.log:
                self.log.debug('executing {0}'.format(cmd))
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as err:
            #
            # rsync return code 23: Partial transfer due to error
            # rsync return code 24: Partial transfer due to missing source files
            #
            if err.returncode in (23, 24):
                msg = 'rsync reports files partially copied'
                if self.log:
                    self.log.warn(msg)
                print >> sys.stderr, 'warning:', msg
            else:
                raise

    def mount(self):
        subprocess.check_call('sync')
        if not os.path.exists(self.mpoint):
            os.makedirs(self.mpoint)
        if self.log:
            self.log.debug("mounting {0}".format(self.mpoint))
        subprocess.check_call(['mount', '-o', 'loop', self.image, self.mpoint])

    def unmount(self):
        subprocess.check_call('sync')
        if self.log:
            self.log.debug("unmounting {0}".format(self.mpoint))
        subprocess.check_call(['umount', '-d', self.mpoint])
        if os.path.exists(self.mpoint):
            os.rmdir(self.mpoint)

    def __enter__(self):
        self.mount()
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_value, traceback):
        self.unmount()


class ImageCreator(object):
    def __init__(self, log=None, **kwargs):
        #
        # Assign settings for image creation
        #
        self.log = log
        self.filesystem = {}
        self.volume = kwargs.get('volume')
        self.fstab = kwargs.get('fstab')
        self.generate_fstab = kwargs.get('generate_fstab', False)
        self.excludes = kwargs.get('exclude', [])
        self.includes = kwargs.get('include', [])
        self.bundle_all_dirs = kwargs.get('bundle_all_dirs', False)
        self.prefix = kwargs.get('prefix')
        self.filter = kwargs.get('filter', True)
        self.size = kwargs.get('size')
        self.destination = kwargs.get('destination') or mkdtemp(prefix='image-')
        self.image = os.path.join(self.destination,
                                  '{0}.img'.format(self.prefix))

        #
        # Validate settings
        #
        if not self.volume:
            raise ValueError("must supply a source volume.")
        self.volume = sanitize_path(self.volume)
        if not self.size:
            raise ValueError("must supply a size for the generated image.")
        if not self.prefix:
            raise ValueError("must supply a prefix.")
        if not self.volume:
            raise ValueError("must supply a volume.")
        if not (os.path.exists(self.destination) or
                os.path.isdir(self.destination)):
            raise ValueError("'{0}' is not a directory or does not exist."
                             .format(self.destination))

    def run(self):
        """
        Prepare a disk image
        """
        print >> sys.stderr, "Creating image...",
        self._create_raw_diskimage()
        self._populate_filesystem_info()
        self._make_filesystem(**self.filesystem)
        print >> sys.stderr, " done"
        #
        # Inside the VolumeSync context we will mount our image
        # as a loop device. If for any reason a failure occurs
        # the device will automatically be unmounted and cleaned up.
        #
        print >> sys.stderr, "Syncing volume contents...",
        with VolumeSync(self.volume, self.image, log=self.log) as volsync:
            if self.fstab:
                volsync.install_fstab_from_file(self.fstab)
            elif self.generate_fstab:
                volsync.generate_fstab()
            if self.filter:
                volsync.filter_files()
            if self.bundle_all_dirs:
                volsync.bundle_all()
            volsync.exclude(self.excludes)
            volsync.include(self.includes)
            volsync.run()
        print >> sys.stderr, " done"

        return self.image

    def _create_raw_diskimage(self):
        """Create a sparse raw image file."""
        subprocess.check_call(['dd', 'if=/dev/zero',
                               'of={0}'.format(self.image), 'count=1', 'bs=1M',
                               'seek={0}'.format(self.size - 1)])

    def _populate_filesystem_info(self):
        """Create a temporary device node for the volume we're going
        to copy. We'll use it to get information about the source volume's
        filesystem.
        """
        st_dev = os.stat(self.volume).st_dev
        devid = os.makedev(os.major(st_dev), os.minor(st_dev))
        directory = mkdtemp(prefix='devnode-')
        devnode = os.path.join(directory, 'rootdev')
        os.mknod(devnode, 0o400 | stat.S_IFBLK, devid)
        try:
            for tag in BLKID_TAGS:
                try:
                    out = subprocess.Popen(['blkid', '-s', tag,
                                            '-ovalue', devnode],
                                           stdout=subprocess.PIPE
                                           ).communicate()[0]
                    self.filesystem[BLKID_TAGS[tag]] = out.rstrip()
                except subprocess.CalledProcessError:
                    pass
        finally:
            os.remove(devnode)
            os.rmdir(directory)

    def _make_filesystem(self, fstype='ext3', uuid=None, label=None):
        """Format our raw image.
        :param fstype: (optional) Filesystem type, one of ext3, ext4, xfs, btrfs.
        :param uuid: (optional) UUID of the filesystem.
        :param label: (optional) Label of the filesystem.
        """
        mkfs_cmd = 'mkfs.{0}'.format(fstype)
        tunefs = None

        if fstype.startswith('ext'):
            mkfs = [mkfs_cmd, '-F', self.image]
            if uuid:
                tunefs = ['tune2fs', '-U', uuid, self.image]
        elif fstype == 'xfs':
            mkfs = [mkfs_cmd, self.image]
            tunefs = ['xfs_admin', '-U', uuid, self.image]
        elif fstype == 'btrfs':
            mkfs = [mkfs_cmd, self.image]
            if uuid:
                raise Exception("btrfs with uuid not supported")
        else:
            raise Exception("unsupported fs {0}".format(fstype))

        if label:
            mkfs.extend(['-L', label])
        subprocess.check_call(mkfs)

        if tunefs:
            subprocess.check_call(tunefs)


def _generate_fstab_content(arch=platform.machine()):
    """Generate an fstab file based on the system's architecture.
    Returns the fstab file contents as a string.
    :param arch: (optional) The architecture to use when creating the fstab
    file. It will default to the architecture of the currently running system.
    If the system is 'i386' then the legacy fstab configuration will be used,
    and if the system is 'x86_64' then the new fstab configuration will be used.
    """
    if arch in FSTAB_BODY_TEMPLATE:
        return "\n".join([FSTAB_HEADER_TEMPLATE.format(
                time.strftime(FSTAB_TIME_FORMAT)),
                FSTAB_BODY_TEMPLATE.get(arch)])
    else:
        raise Exception("platform architecture {0} not supported".format(arch))
