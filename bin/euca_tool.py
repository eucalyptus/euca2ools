import boto
# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Regents of the University of California
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
# Author: Sunil Soman sunils@cs.ucsb.edu

import getopt, sys, os
import boto

def parse_url(url):
    host = url 
    port = None
    service_path = '/'
    url = url.replace('http://', '')
    url = url.replace('https://', '')
    url_parts = url.split(':')
    if (len(url_parts) > 1):
        host = url_parts[0]
        path_parts = url_parts[1].split('/', 1)
	if (len(path_parts) > 1):
	    port = int(path_parts[0])
	    service_path = path_parts[1]
    return host, port, service_path	

def make_connection(ec2_user_access_key=None, ec2_user_secret_key=None, is_secure=False, host=None, 
		    port=None, service=None): 
    return boto.connect_ec2(aws_access_key_id=ec2_user_access_key, 
			        aws_secret_access_key=ec2_user_secret_key,
				is_secure=False,
				host=host,
				port=port,
				service=service)


class EucaTool:
    def __init__(self):
        opts, args = getopt.getopt(sys.argv[1:], 'h',
                                   ['help', 'version', 'debug'])

        self.ec2_user_access_key = os.getenv('EC2_ACCESS_KEY')
        if not self.ec2_user_access_key:
            print 'EC2_ACCESS_KEY environment variable must be set.'
 
        self.ec2_user_secret_key = os.getenv('EC2_SECRET_KEY')
        if not self.ec2_user_secret_key:
            print 'EC2_SECRET_KEY environment variable must be set.'

        self.ec2_url = os.getenv('EC2_URL')
        if not self.ec2_url:
	    print 'EC2_URL must be set.'
	    
    def print_all(self):
	print self.ec2_user_access_key 
