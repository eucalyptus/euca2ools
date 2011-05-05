# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
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
# Author: Neil Soman neil@eucalyptus.com

import os
import shutil
import subprocess
import utils

IMAGE_IO_CHUNK = 10 * 1024
IMAGE_SPLIT_CHUNK = IMAGE_IO_CHUNK * 1024
MAX_LOOP_DEVS = 256

class LinuxImage:

    ALLOWED_FS_TYPES = ['ext2', 'ext3', 'xfs', 'jfs', 'reiserfs']
    BANNED_MOUNTS = ['/dev', '/media', '/mnt', '/proc',
                     '/sys', '/cdrom', '/tmp']
    ESSENTIAL_DIRS = ['proc', 'tmp', 'dev', 'mnt', 'sys']
    ESSENTIAL_DEVS = [[os.path.join('dev', 'console'), 'c', '5', '1'],
                      [os.path.join('dev', 'full'), 'c', '1', '7'],
                      [os.path.join('dev', 'null'), 'c', '1', '3'],
                      [os.path.join('dev', 'zero'), 'c', '1', '5'],
                      [os.path.join('dev', 'tty'), 'c', '5', '0'],
                      [os.path.join('dev', 'tty0'), 'c', '4', '0'],
                      [os.path.join('dev', 'tty1'), 'c', '4', '1'],
                      [os.path.join('dev', 'tty2'), 'c', '4', '2'],
                      [os.path.join('dev', 'tty3'), 'c', '4', '3'],
                      [os.path.join('dev', 'tty4'), 'c', '4', '4'],
                      [os.path.join('dev', 'tty5'), 'c', '4', '5'],
                      [os.path.join('dev', 'xvc0'), 'c', '204', '191']]
    MAKEFS_CMD = 'mkfs.ext3'
    NEW_FSTAB = ['/dev/sda1\t/\text3\tdefaults 1 1',
                 '/dev/sdb\t/mnt\text3\tdefaults 0 0',
                 'none\t/dev/pts\tdevpts\tgid=5,mode=620 0 0',
                 'none\t/proc\tproc\tdefaults 0 0',
                 'none\t/sys\tsysfs\tdefaults 0 0']

    OLD_FSTAB = ['/dev/sda1\t/\text3\tdefaults,errors=remount-ro 0 0',
                 '/dev/sda2\t/mnt\text3\tdefaults\t0 0',
                 '/dev/sda3\tswap\tswap\tdefaults\t0 0',
                 'proc\t/proc\tproc\tdefaults\t0 0',
                 'devpts\t/dev/pts\tdevpts\tgid=5,mode=620  0 0']

    def __init__(self, debug=False):
        self.debug = debug

    def create_image(self, size_in_MB, image_path):
        dd_cmd = ['dd']
        dd_cmd.append('if=/dev/zero')
        dd_cmd.append('of=%s' % image_path)
        dd_cmd.append('count=1')
        dd_cmd.append('bs=1M')
        dd_cmd.append('seek=%s' % (size_in_MB - 1))
        if self.debug:
            print 'Creating disk image...', image_path
        subprocess.Popen(dd_cmd, subprocess.PIPE).communicate()[0]

    def make_fs(self, image_path, fs_type = None, uuid = None, label = None):
        mkfs_prog = self.MAKEFS_CMD
        if fs_type:
            mkfs_prog = "mkfs.%s" % fs_type
        else:
            fs_type = "ext3"

        tunecmd = [ ]
        if fs_type.startswith("ext"):
            mkfs = [ mkfs_prog , '-F', image_path ]
            if uuid:
                tunecmd = [ 'tune2fs', '-U', uuid, image_path ]
            if label: mkfs.extend([ '-L', label ])
        elif fs_type == "xfs":
            mkfs = [ mkfs_prog , image_path ]
            if label: mkfs.extend([ '-L', label ])
            tunecmd = [ 'xfs_admin', '-U', uuid, image_path ]
        elif fs_type == "btrfs":
            if uuid: raise(UnsupportedException("btrfs with uuid not supported"))
            if label: mkfs.extend([ '-L', label ])
        else:
            raise(UnsupportedException("unsupported fs %s" % fs_type))

        utils.check_prerequisite_command(mkfs_prog)

        if self.debug:
            print 'Creating filesystem with %s' % mkfs

        makefs_cmd = subprocess.Popen(mkfs,subprocess.PIPE).communicate()[0]

        if len(tunecmd) > 0:
            utils.check_prerequisite_command(tunecmd[0])
            tune_cmd = subprocess.Popen(tunecmd,subprocess.PIPE).communicate()[0]

    def add_fstab(self, mount_point, generate_fstab, fstab_path):
        if not fstab_path:
            return
        fstab = None
        if fstab_path == 'old':
            if not generate_fstab:
                return
            fstab = '\n'.join(self.OLD_FSTAB)
        elif fstab_path == 'new':
            if not generate_fstab:
                return
            fstab = '\n'.join(self.NEW_FSTAB)

        etc_file_path = os.path.join(mount_point, 'etc')
        fstab_file_path = os.path.join(etc_file_path, 'fstab')
        if not os.path.exists(etc_file_path):
            os.mkdir(etc_file_path)
        else:
            if os.path.exists(fstab_file_path):
                fstab_copy_path = fstab_file_path + '.old'
                shutil.copyfile(fstab_file_path, fstab_copy_path)

        if self.debug:
            print 'Updating fstab entry'
        fstab_file = open(fstab_file_path, 'w')
        if fstab:
            fstab_file.write(fstab)
        else:
            orig_fstab_file = open(fstab_path, 'r')
            while 1:
                data = orig_fstab_file.read(IMAGE_IO_CHUNK)
                if not data:
                    break
                fstab_file.write(data)
            orig_fstab_file.close()
        fstab_file.close()

    def make_essential_devs(self, image_path):
        for entry in self.ESSENTIAL_DEVS:
            cmd = ['mknod']
            entry[0] = os.path.join(image_path, entry[0])
            cmd.extend(entry)
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

class SolarisImage:

    ALLOWED_FS_TYPES = ['ext2', 'ext3', 'xfs', 'jfs', 'reiserfs']
    BANNED_MOUNTS = ['/dev', '/media', '/mnt', '/proc',
                     '/sys', '/cdrom', '/tmp']
    ESSENTIAL_DIRS = ['proc', 'tmp', 'dev', 'mnt', 'sys']

    def __init__(self, debug=False):
        self.debug = debug

    def create_image(self, size_in_MB, image_path):
        print 'Sorry. Solaris not supported yet'
        raise UnsupportedException

    def make_fs(self, image_path, fstype = None, uuid = None, label = None):
        print 'Sorry. Solaris not supported yet'
        raise UnsupportedException

    def make_essential_devs(self, image_path):
        print 'Sorry. Solaris not supported yet'
        raise UnsupportedException


