# Copyright 2009-2014 Eucalyptus Systems, Inc.
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
import os.path
import pipes
import shutil
import subprocess
import sys
import tempfile
import time

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError, ClientError
from requestbuilder.mixins import FileTransferProgressBarMixin
import requests

import euca2ools
from euca2ools.commands import Euca2ools
from euca2ools.commands.argtypes import (delimited_list, filesize,
                                         manifest_block_device_mappings)
from euca2ools.commands.bundle.bundleimage import BundleImage


##IMAGE_MAX_SIZE_IN_MB = Bundle.EC2_IMAGE_SIZE_LIMIT / 1024 // 1024  ## TODO
ALLOWED_FILESYSTEM_TYPES = ['btrfs', 'ext2', 'ext3', 'ext4', 'jfs', 'xfs']
DEFAULT_EXCLUDES_FILE = '/etc/euca2ools/bundle-vol/excludes'
FSTAB_TEMPLATE_FILE = '/etc/euca2ools/bundle-vol/fstab'


## TODO:  rename this module to bundlevolume.py
class BundleVolume(BaseCommand, FileTransferProgressBarMixin):
    SUITE = Euca2ools
    DESCRIPTION = ("Prepare this machine's filesystem for use in the cloud\n\n"
                   "This command must be run as the superuser.")
    REGION_ENVVAR = 'AWS_DEFAULT_REGION'
    ARGS = [Arg('-p', '--prefix', help='''the file name prefix to give the
                bundle's files (default: image)'''),
            Arg('-d', '--destination', metavar='DIR', help='''location to place
                the bundle's files (default:  dir named by TMPDIR, TEMP, or TMP
                environment variables, or otherwise /var/tmp)'''),
            # -r/--arch is required, but to keep the UID check we do at the
            # beginning of configure() first we enforce that there instead.
            Arg('-r', '--arch', help="the image's architecture (required)",
                choices=('i386', 'x86_64', 'armhf', 'ppc', 'ppc64')),
            Arg('-e', '--exclude', metavar='PATH,...', type=delimited_list(','),
                help='comma-separated list of paths to exclude'),
            Arg('-i', '--include', metavar='PATH,...', type=delimited_list(','),
                help='comma-separated list of paths to include'),
            Arg('-s', '--size', metavar='MiB', type=int, default=10240,
                help='size of the image to create (default: 10240 MiB)'),
            Arg('--no-filter', action='store_true',
                help='do not filter out sensitive/system files'),
            Arg('--all', action='store_true',
                help='''include all filesystems regardless of type
                (default: only include local filesystems)'''),
            MutuallyExclusiveArgList(
                Arg('--inherit', dest='inherit', action='store_true',
                    help='''use the metadata service to provide metadata for
                    the bundle (this is the default)'''),
                Arg('--no-inherit', dest='inherit', action='store_false',
                    help='''do not use the metadata service for bundle
                    metadata''')),
            Arg('-v', '--volume', metavar='DIR', default='/', help='''location
                of the volume from which to create the bundle (default: /)'''),
            Arg('-P', '--partition', choices=('mbr', 'gpt', 'none'),
                help='''the type of partition table to create (default: attempt
                to guess based on the existing disk)'''),
            Arg('-S', '--script', metavar='FILE', help='''location of a script
                to run immediately before bundling.  It will receive the
                volume's mount point as its only argument.'''),
            MutuallyExclusiveArgList(
                Arg('--fstab', metavar='FILE', help='''location of an
                    fstab(5) file to copy into the bundled image'''),
                Arg('--generate-fstab', action='store_true',
                    help='''automatically generate an fstab(5) file for
                    the bundled image''')),
            Arg('--grub-config', metavar='FILE', help='''location of a GRUB 1
                configuration file to copy to /boot/grub/menu.lst on the
                bundled image'''),

            # Bundle-related stuff
            Arg('-k', '--privatekey', metavar='FILE', help='''file containing
                your private key to sign the bundle's manifest with.  This
                private key will also be required to unbundle the image in the
                future.'''),
            Arg('-c', '--cert', metavar='FILE',
                help='file containing your X.509 certificate'),
            Arg('--ec2cert', metavar='FILE', help='''file containing the
                cloud's X.509 certificate'''),
            Arg('-u', '--user', metavar='ACCOUNT', help='your account ID'),
            Arg('--kernel', metavar='IMAGE', help='''ID of the kernel image to
                associate with this machine image'''),
            Arg('--ramdisk', metavar='IMAGE', help='''ID of the ramdisk image
                to associate with this machine image'''),
            Arg('-B', '--block-device-mappings',
                metavar='VIRTUAL1=DEVICE1,VIRTUAL2=DEVICE2,...',
                type=manifest_block_device_mappings,
                help='''block device mapping scheme with which to launch
                instances of this machine image'''),
            Arg('--productcodes', metavar='CODE1,CODE2,...',
                type=delimited_list(','), default=[],
                help='comma-separated list of product codes for the image'),
            Arg('--part-size', type=filesize, default=10485760,
                help=argparse.SUPPRESS),
            Arg('--enc-key', type=(lambda s: int(s, 16)),
                help=argparse.SUPPRESS),
            Arg('--enc-iv', type=(lambda s: int(s, 16)),
                help=argparse.SUPPRESS)]

    def configure(self):
        if os.geteuid() != 0:
            raise RuntimeError('must be superuser')

        if not self.args.get('arch'):
            raise ArgumentError('argument -r/--arch is required')

        # Farm all the bundle arg validation out to BundleImage
        self.__build_bundle_command('/dev/null', image_size=1)

        root_device = _get_root_device()
        if self.args.get('inherit'):
            self.__populate_args_from_metadata()
        if not self.args.get('partition'):
            self.args['partition'] = _get_partition_table_type(root_device)
            if not self.args['partition']:
                self.log.warn('could not determine the partition table type '
                              'for root device %s', root_device)
                raise ArgumentError(
                    'could not determine the type of partition table to use; '
                    'specify one with -P/--partition'.format(root_device))
            self.log.info('discovered partition table type %s',
                          self.args['partition'])
        if not self.args.get('fstab') and not self.args.get('generate_fstab'):
            self.args['fstab'] = '/etc/fstab'

    def main(self):
        if self.args.get('destination'):
            destdir = self.args['destination']
        else:
            destdir = euca2ools.util.mkdtemp_for_large_files(prefix='bundle-')
        image = os.path.join(destdir, self.args.get('prefix') or 'image')
        mountpoint = tempfile.mkdtemp(prefix='target-', dir=destdir)

        # Prepare the disk image
        device = self.__create_disk_image(image, self.args['size'])
        try:
            self.__create_and_mount_filesystem(device, mountpoint)
            try:
                # Copy files
                exclude_opts = self.__get_exclude_and_include_args()
                exclude_opts.extend(['--exclude', image,
                                     '--exclude', mountpoint])
                self.__copy_to_target_dir(mountpoint, exclude_opts)
                self.__insert_fstab(mountpoint)
                self.__insert_grub_config(mountpoint)
                if self.args.get('script'):
                    cmd = [self.args['script'], mountpoint]
                    self.log.info("running user script ``%s''",
                                  _quote_cmd(cmd))
                    subprocess.check_call(cmd)

            except KeyboardInterrupt:
                self.log.info('received ^C; skipping to cleanup')
                msg = ('Cleaning up after ^C -- pressing ^C again will '
                       'result in the need for manual device cleanup')
                print >> sys.stderr, msg
                raise
            # Cleanup
            finally:
                time.sleep(0.2)
                self.__unmount_filesystem(device)
                os.rmdir(mountpoint)
        finally:
            self.__detach_disk_image(image, device)

        bundle_cmd = self.__build_bundle_command(image)
        result = bundle_cmd.main()
        os.remove(image)
        return result

    def print_result(self, result):
        for manifest_filename in result[1]:
            print 'Wrote manifest', manifest_filename

    def __build_bundle_command(self, image_filename, image_size=None):
        bundle_args = ('prefix', 'destination', 'arch', 'privatekey', 'cert',
                       'ec2cert', 'user', 'kernel', 'ramdisk',
                       'block_device_mappings', 'productcodes', 'part_size',
                       'enc_key', 'enc_iv', 'show_progress')
        bundle_args_dict = dict((key, self.args.get(key))
                                for key in bundle_args)
        return BundleImage.from_other(self, image=image_filename,
                                      image_size=image_size,
                                      image_type='machine', **bundle_args_dict)

    ### INSTANCE METADATA ###

    def __read_metadata_value(self, path):
        self.log.debug("reading metadata service value '%s'", path)
        url = 'http://169.254.169.254/2012-01-12/meta-data/' + path
        response = requests.get(url, timeout=1)
        if response.status_code == 200:
            return response.text
        return None

    def __read_metadata_list(self, path):
        value = self.__read_metadata_value(path)
        if value:
            return [line.rstrip('/') for line in value.splitlines() if line]
        return []

    def __read_metadata_dict(self, path):
        metadata = {}
        if not path.endswith('/'):
            path += '/'
        keys = self.__read_metadata_list(path)
        for key in keys:
            if key:
                metadata[key] = self.__read_metadata_value(path + key)
        return metadata

    def __populate_args_from_metadata(self):
        """
        Populate missing/empty values in self.args using info obtained
        from the metadata service.
        """
        try:
            if not self.args.get('kernel'):
                self.args['kernel'] = self.__read_metadata_value('kernel-id')
                self.log.info('inherited kernel: %s', self.args['kernel'])
            if not self.args.get('ramdisk'):
                self.args['ramdisk'] = self.__read_metadata_value('ramdisk-id')
                self.log.info('inherited ramdisk: %s', self.args['ramdisk'])
            if not self.args.get('productcodes'):
                self.args['productcodes'] = self.__read_metadata_list(
                    'product-codes')
                if self.args['productcodes']:
                    self.log.info('inherited product codes: %s',
                                  ','.join(self.args['productcodes']))
            if not self.args.get('block_device_mappings'):
                self.args['block_device_mappings'] = {}
                for key, val in (self.__read_metadata_dict(
                        'block-device-mapping') or {}).iteritems():
                    if not key.startswith('ebs'):
                        self.args['block_device_mappings'][key] = val
                for key, val in self.args['block_device_mappings'].iteritems():
                    self.log.info('inherited block device mapping: %s=%s',
                                  key, val)
        except requests.exceptions.Timeout:
            raise ClientError('metadata service is absent or unresponsive; '
                              'use --no-inherit to proceed without it')

    ### DISK MANAGEMENT ###

    def __create_disk_image(self, image, size_in_mb):
        subprocess.check_call(['dd', 'if=/dev/zero', 'of={0}'.format(image),
                               'bs=1M', 'count=1',
                               'seek={0}'.format(int(size_in_mb) - 1)])
        if self.args['partition'] == 'mbr':
            # Why use sfdisk when we can use parted?  :-)
            parted_script = (
                b'unit s', b'mklabel msdos', b'mkpart primary 64 -1s',
                b'set 1 boot on', b'print', b'quit')
            subprocess.check_call(['parted', '-s', image, '--',
                                   ' '.join(parted_script)])
        elif self.args['partition'] == 'gpt':
            # type 0xef02 == BIOS boot (we'll put it at the end of the list)
            subprocess.check_call(
                ['sgdisk', '--new', '128:1M:+1M', '--typecode', '128:ef02',
                 '--change-name', '128:BIOS Boot', image])
            # type 0x8300 == Linux filesystem data
            subprocess.check_call(
                ['sgdisk', '--largest-new=1', '--typecode', '1:8300',
                 '--change-name', '1:Image', image])
            subprocess.check_call(['sgdisk', '--print', image])

        mapped = self.__map_disk_image(image)
        assert os.path.exists(mapped)
        return mapped

    def __map_disk_image(self, image):
        if self.args['partition'] in ('mbr', 'gpt'):
            # Create /dev/mapper/loopXpY and return that.
            # We could do this with losetup -Pf as well, but that isn't
            # available on RHEL 6.
            self.log.debug('mapping partitioned image %s', image)
            kpartx = subprocess.Popen(['kpartx', '-s', '-v', '-a', image],
                                      stdout=subprocess.PIPE)
            try:
                for line in kpartx.stdout.readlines():
                    line_split = line.split()
                    if line_split[:2] == ['add', 'map']:
                        device = line_split[2]
                        if device.endswith('p1'):
                            return '/dev/mapper/{0}'.format(device)
                self.log.error('failed to get usable map output from kpartx')
                raise RuntimeError('device mapping failed')
            finally:
                # Make sure the process exits
                kpartx.communicate()
        else:
            # No partition table
            self.log.debug('mapping unpartitioned image %s', image)
            losetup = subprocess.Popen(['losetup', '-f', image, '--show'],
                                       stdout=subprocess.PIPE)
            loopdev, _ = losetup.communicate()
            return loopdev.strip()

    def __create_and_mount_filesystem(self, device, mountpoint):
        root_device = _get_root_device()
        fsinfo = _get_filesystem_info(root_device)
        self.log.info('creating filesystem on %s using metadata from %s: %s',
                      device, root_device, fsinfo)
        fs_cmds = [['mkfs', '-t', fsinfo['type']]]
        if fsinfo.get('label'):
            fs_cmds[0].extend(['-L', fsinfo['label']])
        elif fsinfo['type'] in ('ext2', 'ext3', 'ext4'):
            if fsinfo.get('uuid'):
                fs_cmds[0].extend(['-U', fsinfo['uuid']])
            # Time-based checking doesn't make much sense for cloud images
            fs_cmds.append(['tune2fs', '-i', '0'])
        elif fsinfo['type'] == 'jfs':
            if fsinfo.get('uuid'):
                fs_cmds.append(['jfs_tune', '-U', fsinfo['uuid']])
        elif fsinfo['type'] == 'xfs':
            if fsinfo.get('uuid'):
                fs_cmds.append(['xfs_admin', '-U', fsinfo['uuid']])
        for fs_cmd in fs_cmds:
            fs_cmd.append(device)
            self.log.info("formatting with ``%s''", _quote_cmd(fs_cmd))
            subprocess.check_call(fs_cmd)
        self.log.info('mounting %s filesystem %s at %s', fsinfo['type'],
                      device, mountpoint)
        subprocess.check_call(['mount', '-t', fsinfo['type'], device,
                               mountpoint])

    def __unmount_filesystem(self, device):
        self.log.info('unmounting %s', device)
        subprocess.check_call(['sync'])
        time.sleep(0.2)
        subprocess.check_call(['umount', device])

    def __detach_disk_image(self, image, device):
        if self.args['partition'] in ('mbr', 'gpt'):
            self.log.debug('unmapping partitioned image %s', image)
            cmd = ['kpartx', '-s', '-d', image]
        else:
            self.log.debug('unmapping unpartitioned device %s', device)
            cmd = ['losetup', '-d', device]
        subprocess.check_call(cmd)

    ### FILE MANAGEMENT ###

    def __get_exclude_and_include_args(self):
        args = []
        for exclude in (self.args.get('exclude') or []):
            args.extend(['--exclude', exclude])
        for include in (self.args.get('include') or []):
            args.extend(['--include', include])
        # Exclude remote filesystems
        if not self.args.get('all'):
            for device, mountpoint, fstype in _get_all_mounts():
                if fstype not in ALLOWED_FILESYSTEM_TYPES:
                    self.log.debug('excluding %s filesystem %s at %s',
                                   fstype, device, mountpoint)
                    args.extend(['--exclude', os.path.join(mountpoint, '**')])
        # Add pre-defined exclusions
        ## TODO:  stuff that file in setup.py
        ## TODO:  decide whether that envvar is the right place for user conf
        excludes_filename = os.getenv('EUCA_BUNDLE_VOL_EXCLUDES_FILE',
                                      DEFAULT_EXCLUDES_FILE)
        if not self.args.get('no_filter') and os.path.isfile(excludes_filename):
            self.log.debug('adding path exclusions from %s', excludes_filename)
            args.extend(['--exclude-from', excludes_filename])
        return args

    def __copy_to_target_dir(self, dest, exclude_opts):
        source = self.args.get('volume') or '/'
        if not source.endswith('/'):
            source += '/'
        if not dest.endswith('/'):
            dest += '/'

        rsync_opts = ['-rHlpogDtS']
        if self.args.get('show_progress'):
            rsync = subprocess.Popen(['rsync', '--version'],
                                      stdout=subprocess.PIPE)
            out, _ = rsync.communicate()
            rsync_version = (out.partition('version ')[2] or '\0').split()[0]
            if rsync_version >= '3.1.0':
                # Use the new summarizing version
                rsync_opts.append('--info=progress2')
            else:
                rsync_opts.append('--progress')
        else:
            rsync_opts.append('--quiet')
        cmd = ['rsync', '-X'] + rsync_opts + exclude_opts + [source, dest]
        self.log.info("copying files with ``%s''", _quote_cmd(cmd))
        print 'Copying files...'
        rsync = subprocess.Popen(cmd)
        rsync.wait()
        if rsync.returncode == 1:
            # Try again without xattrs
            self.log.info('rsync exited with code %i; retrying without xattrs',
                          rsync.returncode)
            print 'Retrying without extended attributes'
            cmd = ['rsync'] + rsync_opts + exclude_opts + [source, dest]
            rsync = subprocess.Popen(cmd)
            rsync.wait()
        if rsync.returncode not in (0, 23):
            self.log.error('rsync exited with code %i', rsync.returncode)
            raise subprocess.CalledProcessError(rsync.returncode, 'rsync')

    def __insert_fstab(self, mountpoint):
        fstab_filename = os.path.join(mountpoint, 'etc', 'fstab')
        if os.path.exists(fstab_filename):
            fstab_bak = fstab_filename + '.bak'
            self.log.debug('backing up original fstab file as %s', fstab_bak)
            _copy_with_xattrs(fstab_filename, fstab_bak)
        if self.args.get('generate_fstab'):
            # This isn't really a template, but if the need arises we
            # can add something of that sort later.
            self.log.info('generating fstab file from %s', self.args['fstab'])
            _copy_with_xattrs(FSTAB_TEMPLATE_FILE, fstab_filename)
        elif self.args.get('fstab'):
            self.log.info('using fstab file %s', self.args['fstab'])
            _copy_with_xattrs(self.args['fstab'], fstab_filename)

    def __insert_grub_config(self, mountpoint):
        if self.args.get('grub_config'):
            grub_filename = os.path.join(mountpoint, 'boot', 'grub',
                                         'menu.lst')
            if os.path.exists(grub_filename):
                grub_back = grub_filename + '.bak'
                self.log.debug('backing up original grub1 config file as %s',
                               grub_back)
                _copy_with_xattrs(grub_filename, grub_back)
            self.log.info('using grub1 config file %s',
                          self.args['grub_config'])
            _copy_with_xattrs(self.args['grub_config'], grub_filename)


def _get_all_mounts():
    # This implementation is Linux-specific

    # We first load everything into a dict based on mount points so we
    # can return only the last filesystem to be mounted in each
    # location.  This is important for / on Linux, where a rootfs
    # volume has a real filesystem mounted on top of it, because
    # returning both of them will cause / to get excluded due to its
    # filesystem type.
    filesystems_dict = {}
    with open('/proc/mounts') as mounts:
        for line in mounts:
            device, mountpoint, fstype, _ = line.split(None, 3)
            filesystems_dict[mountpoint] = (device, fstype)
    filesystems_list = []
    for mountpoint, (device, fstype) in filesystems_dict.iteritems():
        filesystems_list.append((device, mountpoint, fstype))
    return filesystems_list


def _get_filesystem_info(device):
    blkid = subprocess.Popen(['blkid', '-d', '-o', 'export', device],
                             stdout=subprocess.PIPE)
    fsinfo = {}
    for line in blkid.stdout:
        key, _, val = line.strip().partition('=')
        if key == 'LABEL':
            fsinfo['label'] = val
        elif key == 'TYPE':
            fsinfo['type'] = val
        elif key == 'UUID':
            fsinfo['uuid'] = val
    blkid.wait()
    return fsinfo


def _get_partition_table_type(device, debug=False):
    if device[-1] in '0123456789':
        if device[-2] == 'd':
            # /dev/sda1, /dev/xvda1, /dev/vda1, etc.
            device = device[:-1]
        elif device[-2] == 'p':
            # /dev/loop0p1, /dev/sr0p1, etc.
            device = device[:-2]
    if debug:
        stderr_dest = subprocess.PIPE
    else:
        stderr_dest = None
    parted = subprocess.Popen(['parted', '-m', '-s', device, 'print'],
                              stdout=subprocess.PIPE, stderr=stderr_dest)
    stdout, _ = parted.communicate()
    for line in stdout:
        if line.startswith('/dev/'):
            # /dev/sda:500GB:scsi:512:512:msdos:ATA WDC WD5003ABYX-1;
            line_bits = line.split(':')
            if line_bits[5] == 'msdos':
                return 'mbr'
            elif line_bits[5] == 'gpt':
                return 'gpt'
            else:
                return 'none'


def _get_root_device():
    for device, mountpoint, _ in _get_all_mounts():
        if mountpoint == '/' and os.path.exists(device):
            root_device = device
            # Do not skip the rest of the mount points.  Another
            # / filesystem, such as a btrfs subvolume, may be
            # mounted on top of that.
    return root_device


def _quote_cmd(cmd):
    return ' '.join(pipes.quote(arg) for arg in cmd)


def _copy_with_xattrs(source, dest):
    """
    shutil.copy2 doesn't preserve xattrs until python 3.3, so here we
    attempt to leverage the cp command to do it for us.
    """
    try:
        subprocess.check_call(['cp', '-a', source, dest])
    except subprocess.CalledProcessError:
        shutil.copy2(source, dest)
