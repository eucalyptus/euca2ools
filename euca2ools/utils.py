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
# Author: Neil Soman neil@eucalyptus.com
#         Mitch Garnaat mgarnaat@eucalyptus.com

import base64
import os
import sys
import tempfile
from euca2ools import exceptions, __version__


def sanitize_path(path):
    """Make a fully expanded and absolute path for us to work with.
    Returns a santized path string.
    :param path: The path string to sanitize.
    """
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))


def parse_config(config, dict, keylist):
    fmt = ''
    str = ''
    for v in keylist:
        str = '%s "${%s}" ' % (str, v)
        fmt = fmt + '%s%s' % ('%s', '\\0')

    cmd = ['bash', '-ec', ". '%s' >/dev/null; printf '%s' %s"
           % (config, fmt, str)]

    (out, err, retval) = execute(cmd, exception=False)

    if retval != 0:
        raise exceptions.ParseError('Parsing config file %s failed:\n\t%s'
                         % (config, stderr))

    values = stdout.split("\0")
    for i in range(len(values) - 1):
        if values[i] != '':
            dict[keylist[i]] = values[i]


def print_instances(instances, nil=""):

    # I was not able to correctly identify fields with an 'xx' below the
    # descriptions at
    # http://docs.amazonwebservices.com/AWSEC2/latest/CommandLineReference/ApiReference-cmd-DescribeInstances.html
    # were not sufficiently detailed, even when coupled with some limited
    # experimentation
    #
    # Additionally, in order to get 'hypervisor', the api request version
    # in the make_ec2_connection method would need to be increased.
    members=( "id", "image_id", "public_dns_name", "private_dns_name",
        "state", "key_name", "ami_launch_index", "product_codes",
        "instance_type", "launch_time", "placement", "kernel",
        "ramdisk", "xx", "_monitoring", 'ip_address', 'private_ip_address',
        "vpc_id", "subnet_id", "root_device_type", "xx", "xx", "xx", "xx",
        "virtualizationType", "hypervisor", "xx", "_groupnames", "_groupids" )

    for instance in instances:
        # in old describe-instances, there was a check for 'if instance:'
        # I (smoser) have carried this over, but dont know how instance
        # could be false
        if not instance: continue
        items=[ ]
        for member in members:
            # boto's "monitoring" item is blank string
            if member == "_monitoring":
                if instance.monitored:
                    val = "monitoring-enabled"
                else:
                    val = "monitoring-disabled"
            elif member == "_groupids":
                val = [x.name for x in instance.groups]
            elif member == "_groupnames":
                val = [x.id for x in instance.groups]
            else:
                val = getattr(instance,member,nil)

            # product_codes is a list
            if val is None: val = nil
            if hasattr(val,'__iter__'):
                val = ','.join(val)
            items.append(val)
        print "INSTANCE\t%s" % '\t'.join(items)
        if hasattr(instance, 'tags') and isinstance(instance.tags, dict):
            for tag in instance.tags:
                print '\t'.join(('TAG', 'instance', instance.id, tag,
                                 instance.tags[tag]))


def print_version_if_necessary():
    """
    If '--version' appears in sys.argv then print the version and exit
    successfully.

    This is a hackish workaround for a roboto limitation in boto 2.1.1.
    """
    if '--version' in sys.argv:
        print 'euca2ools %s (Sparta)' % __version__
        if os.path.isfile('/etc/eucalyptus/eucalyptus-version'):
            with open('/etc/eucalyptus/eucalyptus-version') as version_file:
                print 'eucalyptus %s' % version_file.readline().strip()
        sys.exit()


def handle_availability_zones(requested_zones, response=None):
    msg = base64.b64decode(
        'ICAgICAgICAgICAgICAgICAgX19fXyAgICAKICAgICAgLi0tLS0tLS0tLS0nI'
        'CAgICctLgogICAgIC8gIC4gICAgICAnICAgICAuICAgXCAgCiAgICAvICAgIC'
        'AgICAnICAgIC4gICAgICAvfAogICAvICAgICAgLiAgICAgICAgICAgICBcIC8'
        'gICAgIAogIC8gICcgLiAgICAgICAuICAgICAuICB8fCB8IAogLy5fX19fX19f'
        'X19fXyAgICAnICAgIC8gLy8KIHwuXyAgICAgICAgICAnLS0tLS0tJ3wgL3wKI'
        'CcuLi4uLi4uLi4uLi4uX19fX19fLi0nIC8KIHwtLiAgICAgICAgICAgICAgIC'
        'AgIHwgLyAgICAgCiBgIiIiIiIiIiIiIiIiIi0uLi4uLi0n')
    if ((response is None or
         len(response.get('availabilityZoneInfo', [])) == 0) and
        'sandwich' in requested_zones):
        # humor dfed
        print >> sys.stderr, msg


def build_progressbar_label_template(fnames):
    if len(fnames) == 0:
        return None
    elif len(fnames) == 1:
        return '{fname}'
    else:
        max_fname_len = max(len(os.path.basename(fname)) for fname in fnames)
        fmt_template = '{{fname:<{maxlen}}} ({{index:>{lenlen}}}/{total})'
        return fmt_template.format(maxlen=max_fname_len,
                                   lenlen=len(str(len(fnames))),
                                   total=len(fnames))


def mkdtemp_for_large_files(suffix='', prefix='tmp', dir=None):
    '''
    Like tempfile.mkdtemp, but using /var/tmp as a last resort instead of /tmp.

    This is meant for utilities that create large files, as /tmp is often a
    ramdisk.
    '''

    if dir is None:
        dir = (os.getenv('TMPDIR') or os.getenv('TEMP') or os.getenv('TMP') or
               '/var/tmp')
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
