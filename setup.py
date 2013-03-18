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

from distutils.command.build_py import build_py
from distutils.command.build_scripts import build_scripts
from distutils.command.install_scripts import install_scripts
from distutils.command.sdist import sdist
import os.path
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from euca2ools import __version__


# Cheap hack:  install symlinks separately from regular files.
# cmd.copy_tree accepts a preserve_symlinks option, but when we call
# ``setup.py install'' more than once the method fails when it encounters
# symlinks that are already there.

class build_scripts_except_symlinks(build_scripts):
    '''Like build_scripts, but ignoring symlinks'''
    def copy_scripts(self):
        orig_scripts = self.scripts
        self.scripts = [script for script in self.scripts
                        if not os.path.islink(script)]
        build_scripts.copy_scripts(self)
        self.scripts = orig_scripts


class install_scripts_and_symlinks(install_scripts):
    '''Like install_scripts, but also replicating nonexistent symlinks'''
    def run(self):
        install_scripts.run(self)
        # Replicate symlinks if they don't exist
        for script in self.distribution.scripts:
            if os.path.islink(script):
                target  = os.readlink(script)
                newlink = os.path.join(self.install_dir, os.path.basename(script))
                if not os.path.exists(newlink):
                    os.symlink(target, newlink)


class build_py_with_git_version(build_py):
    '''Like build_py, but also hardcoding the version in __init__.__version__
       so it's consistent even outside of the source tree'''

    def build_module(self, module, module_file, package):
        build_py.build_module(self, module, module_file, package)
        print module, module_file, package
        if module == '__init__' and '.' not in package:
            version_line = "__version__ = '{0}'\n".format(__version__)
            old_init_name = self.get_module_outfile(self.build_lib, (package,),
                                                    module)
            new_init_name = old_init_name + '.new'
            with open(new_init_name, 'w') as new_init:
                with open(old_init_name) as old_init:
                    for line in old_init:
                        if line.startswith('__version__ ='):
                            new_init.write(version_line)
                        else:
                            new_init.write(line)
                new_init.flush()
            os.rename(new_init_name, old_init_name)


class sdist_with_git_version(sdist):
    '''Like sdist, but also hardcoding the version in __init__.__version__ so
       it's consistent even outside of the source tree'''

    def make_release_tree(self, base_dir, files):
        sdist.make_release_tree(self, base_dir, files)
        version_line = "__version__ = '{0}'\n".format(__version__)
        old_init_name = os.path.join(base_dir, 'euca2ools/__init__.py')
        new_init_name = old_init_name + '.new'
        with open(new_init_name, 'w') as new_init:
            with open(old_init_name) as old_init:
                for line in old_init:
                    if line.startswith('__version__ ='):
                        new_init.write(version_line)
                    else:
                        new_init.write(line)
            new_init.flush()
        os.rename(new_init_name, old_init_name)


setup(name = "euca2ools",
      version = __version__,
      description = "Elastic Utility Computing Architecture Command Line Tools",
      long_description="Elastic Utility Computing Architecture Command Line Tools",
      author = "Eucalyptus Systems, Inc.",
      author_email = "support@eucalyptus.com",

      scripts = ["bin/euare-accountaliascreate",
                 "bin/euare-accountaliasdelete",
                 "bin/euare-accountaliaslist",
                 "bin/euare-accountcreate",
                 "bin/euare-accountdel",
                 "bin/euare-accountdelpolicy",
                 "bin/euare-accountgetpolicy",
                 "bin/euare-accountgetsummary",
                 "bin/euare-accountlist",
                 "bin/euare-accountlistpolicies",
                 "bin/euare-accountuploadpolicy",
                 "bin/euare-getldapsyncstatus",
                 "bin/euare-groupaddpolicy",
                 "bin/euare-groupadduser",
                 "bin/euare-groupcreate",
                 "bin/euare-groupdel",
                 "bin/euare-groupdelpolicy",
                 "bin/euare-groupgetpolicy",
                 "bin/euare-grouplistbypath",
                 "bin/euare-grouplistpolicies",
                 "bin/euare-grouplistusers",
                 "bin/euare-groupmod",
                 "bin/euare-groupremoveuser",
                 "bin/euare-groupuploadpolicy",
                 "bin/euare-servercertdel",
                 "bin/euare-servercertgetattributes",
                 "bin/euare-servercertlistbypath",
                 "bin/euare-servercertmod",
                 "bin/euare-servercertupload",
                 "bin/euare-useraddcert",
                 "bin/euare-useraddkey",
                 "bin/euare-useraddloginprofile",
                 "bin/euare-useraddpolicy",
                 "bin/euare-usercreate",
                 "bin/euare-usercreatecert",
                 "bin/euare-userdeactivatemfadevice",
                 "bin/euare-userdel",
                 "bin/euare-userdelcert",
                 "bin/euare-userdelkey",
                 "bin/euare-userdelloginprofile",
                 "bin/euare-userdelpolicy",
                 "bin/euare-userenablemfadevice",
                 "bin/euare-usergetattributes",
                 "bin/euare-usergetinfo",
                 "bin/euare-usergetloginprofile",
                 "bin/euare-usergetpolicy",
                 "bin/euare-userlistbypath",
                 "bin/euare-userlistcerts",
                 "bin/euare-userlistgroups",
                 "bin/euare-userlistkeys",
                 "bin/euare-userlistmfadevices",
                 "bin/euare-userlistpolicies",
                 "bin/euare-usermod",
                 "bin/euare-usermodcert",
                 "bin/euare-usermodkey",
                 "bin/euare-usermodloginprofile",
                 "bin/euare-userresyncmfadevice",
                 "bin/euare-userupdateinfo",
                 "bin/euare-useruploadpolicy",
                 "bin/euca-allocate-address",
                 "bin/euca-associate-address",
                 "bin/euca-attach-volume",
                 "bin/euca-authorize",
                 "bin/euca-bundle-image",
                 "bin/euca-bundle-instance",
                 "bin/euca-bundle-upload",
                 "bin/euca-bundle-vol",
                 "bin/euca-cancel-bundle-task",
                 "bin/euca-check-bucket",
                 "bin/euca-confirm-product-instance",
                 "bin/euca-create-group",
                 "bin/euca-create-image",
                 "bin/euca-create-keypair",
                 "bin/euca-create-snapshot",
                 "bin/euca-create-tags",
                 "bin/euca-create-volume",
                 "bin/euca-delete-bundle",
                 "bin/euca-delete-group",
                 "bin/euca-delete-keypair",
                 "bin/euca-delete-snapshot",
                 "bin/euca-delete-tags",
                 "bin/euca-delete-volume",
                 "bin/euca-deregister",
                 "bin/euca-describe-addresses",
                 "bin/euca-describe-availability-zones",
                 "bin/euca-describe-bundle-tasks",
                 "bin/euca-describe-group",
                 "bin/euca-describe-groups",
                 "bin/euca-describe-image-attribute",
                 "bin/euca-describe-images",
                 "bin/euca-describe-instances",
                 "bin/euca-describe-keypairs",
                 "bin/euca-describe-regions",
                 "bin/euca-describe-snapshots",
                 "bin/euca-describe-tags",
                 "bin/euca-describe-volumes",
                 "bin/euca-detach-volume",
                 "bin/euca-disassociate-address",
                 "bin/euca-download-bundle",
                 "bin/euca-get-console-output",
                 "bin/euca-get-password",
                 "bin/euca-get-password-data",
                 "bin/euca-import-keypair",
                 "bin/euca-modify-image-attribute",
                 "bin/euca-monitor-instances",
                 "bin/euca-reboot-instances",
                 "bin/euca-register",
                 "bin/euca-release-address",
                 "bin/euca-reset-image-attribute",
                 "bin/euca-revoke",
                 "bin/euca-run-instances",
                 "bin/euca-start-instances",
                 "bin/euca-stop-instances",
                 "bin/euca-terminate-instances",
                 "bin/euca-unbundle",
                 "bin/euca-unmonitor-instances",
                 "bin/euca-upload-bundle",
                 "bin/euca-version",
                 "bin/euscale-create-auto-scaling-group",
                 "bin/euscale-create-launch-config",
                 "bin/euscale-delete-auto-scaling-group",
                 "bin/euscale-delete-launch-config",
                 "bin/euscale-delete-notification-configuration",
                 "bin/euscale-delete-policy",
                 "bin/euscale-delete-scheduled-action",
                 "bin/euscale-describe-adjustment-types",
                 "bin/euscale-describe-auto-scaling-groups",
                 "bin/euscale-describe-auto-scaling-instances",
                 "bin/euscale-describe-auto-scaling-notification-types",
                 "bin/euscale-describe-launch-configs",
                 "bin/euscale-describe-metric-collection-types",
                 "bin/euscale-describe-notification-configurations",
                 "bin/euscale-describe-policies",
                 "bin/euscale-describe-process-types",
                 "bin/euscale-describe-scaling-activities",
                 "bin/euscale-describe-scheduled-actions",
                 "bin/euscale-describe-termination-policy-types",
                 "bin/euscale-disable-metrics-collection",
                 "bin/euscale-enable-metrics-collection",
                 "bin/euscale-execute-policy",
                 "bin/euscale-put-notification-configuration",
                 "bin/euscale-put-scaling-policy",
                 "bin/euscale-put-scheduled-update-group-action",
                 "bin/euscale-resume-processes",
                 "bin/euscale-set-desired-capacity",
                 "bin/euscale-set-instance-health",
                 "bin/euscale-suspend-processes",
                 "bin/euscale-terminate-instance-in-auto-scaling-group",
                 "bin/euscale-update-auto-scaling-group",
                 "bin/eustore-describe-images",
                 "bin/eustore-install-image"],
      url = "http://open.eucalyptus.com",
      packages = ["euca2ools",
                  "euca2ools.nc",
                  "euca2ools.commands",
                  "euca2ools.commands.autoscaling",
                  "euca2ools.commands.bundle",
                  "euca2ools.commands.euca",
                  "euca2ools.commands.euare",
                  "euca2ools.commands.autoscaling",
                  "euca2ools.commands.eustore",
                  "euca2ools.commands.walrus"],
      license = 'BSD (Simplified)',
      platforms = 'Posix; MacOS X',
      classifiers = ['Development Status :: 3 - Alpha',
                     'Intended Audience :: Developers',
                     'Intended Audience :: System Administrators',
                     'License :: OSI Approved :: Simplified BSD License',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2',
                     'Programming Language :: Python :: 2.6',
                     'Programming Language :: Python :: 2.7',
                     'Topic :: Internet'],
      cmdclass = {'build_py':        build_py_with_git_version,
                  'build_scripts':   build_scripts_except_symlinks,
                  'install_scripts': install_scripts_and_symlinks,
                  'sdist':           sdist_with_git_version})
