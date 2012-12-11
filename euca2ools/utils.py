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
#         Mitch Garnaat mgarnaat@eucalyptus.com

import os.path
import subprocess
import sys
from euca2ools import exceptions, __version__, __codename__

def check_prerequisite_command(command):
    cmd = [command]
    try:
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE).communicate()
    except OSError, e:
        error_string = '%s' % e
        if 'No such' in error_string:
            print >> sys.stderr, 'Command %s not found. Is it installed?' % command
            raise exceptions.NotFoundError
        else:
            raise OSError(e)

def parse_config(config, dict, keylist):
    fmt = ''
    str = ''
    for v in keylist:
        str = '%s "${%s}" ' % (str, v)
        fmt = fmt + '%s%s' % ('%s', '\\0')

    cmd = ['bash', '-ec', ". '%s' >/dev/null; printf '%s' %s"
           % (config, fmt, str)]

    handle = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, stderr) = handle.communicate()
    if handle.returncode != 0:
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
        print 'euca2ools %s (%s)' % (__version__, __codename__)
        if os.path.isfile('/etc/eucalyptus/eucalyptus-version'):
            with open('/etc/eucalyptus/eucalyptus-version') as version_file:
                print 'eucalyptus %s' % version_file.readline().strip()
        sys.exit()
