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

import subprocess
from euca2ools import exceptions

def check_prerequisite_command(command):
    cmd = [command]
    try:
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE).communicate()
    except OSError, e:
        error_string = '%s' % e
        if 'No such' in error_string:
            print 'Command %s not found. Is it installed?' % command
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
    members=( "id", "image_id", "public_dns_name", "private_dns_name",
        "state", "key_name", "ami_launch_index", "product_codes",
        "instance_type", "launch_time", "placement", "kernel",
        "ramdisk" )

    for instance in instances:
        # in old describe-instances, there was a check for 'if instance:'
        # I (smoser) have carried this over, but dont know how instance
        # could be false
        if not instance: continue
        items=[ ]
        for member in members:
            val = getattr(instance,member,nil)
            # product_codes is a list
            if val is None: val = nil
            if hasattr(val,'__iter__'):
                val = ','.join(val)
            items.append(val)
        print "INSTANCE\t%s" % '\t'.join(items)


