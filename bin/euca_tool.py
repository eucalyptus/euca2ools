# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Regents of the University of California
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

usage_string = """
	-K, --access-key - user's Access Key ID.
 	-S, --secret-key - user's Secret Key.
	-U, --url - Cloud URL.
	-h, --help - Display this help message.
	--version - Display the version of this tool.
	--debug - Turn on debugging.
"""     

def usage():
    print usage_string
    sys.exit()


class EucaTool:
    default_ec2_url = 'http://localhost:8773/services/Eucalyptus'
   
    def process_args(self):
        ids = []
        for arg in self.args:
            ids.append(arg)
        return ids 

    def parse_url(self):
        self.host = self.url 
        self.port = None
        self.service_path = '/'
        url = url.replace('http://', '')
        url = url.replace('https://', '')
        url_parts = url.split(':')
        if (len(url_parts) > 1):
            self.host = url_parts[0]
            path_parts = url_parts[1].split('/', 1)
    	    if (len(path_parts) > 1):
	        self.port = int(path_parts[0])
	        self.service_path = path_parts[1]
 
    def __init__(self, short_opts=None, long_opts=None):

	self.ec2_user_access_key = None
	self.ec2_user_secret_key = None
	self.ec2_url = None
	if not short_opts:
	    short_opts = ''
	if not long_opts:
	    long_opts = ['']
	short_opts += 'hK:S:U:'
	long_opts += ['access-key=', 'secret-key=', 'url=', 'help', 'version', 'debug']
        opts, args = getopt.getopt(sys.argv[1:], short_opts,
                                  long_opts)
	self.opts = opts
	self.args = args
        for name, value in opts:
            if name in ('-K', '--access-key'):
 		self.ec2_user_access_key = value
	    elif name in ('-S', '--secret-key'):
		self.ec2_user_secret_key = value
	    elif name in ('-U', '--url'):
		self.ec2_url = value
	    elif name in ('--debug'):
		self.debug = True
        
	if not self.ec2_user_access_key:
            self.ec2_user_access_key = os.getenv('EC2_ACCESS_KEY')
 	    if not self.ec2_user_access_key:
                print 'EC2_ACCESS_KEY environment variable must be set.'
     		sys.exit()
 
	if not self.ec2_user_secret_key:
            self.ec2_user_secret_key = os.getenv('EC2_SECRET_KEY')
            if not self.ec2_user_secret_key:
                print 'EC2_SECRET_KEY environment variable must be set.'
		sys.exit()

        if not self.ec2_url:
            self.ec2_url = os.getenv('EC2_URL')
            if not self.ec2_url:
	        self.ec2_url = default_ec2_url
		print 'EC2_URL not specified. Trying %s' % (self.ec2_url)

        self.host = self.ec2_url 
	url = self.ec2_url
        self.port = None
        self.service_path = '/'
        url = url.replace('http://', '')
        url = url.replace('https://', '')
        url_parts = url.split(':')
        if (len(url_parts) > 1):
            self.host = url_parts[0]
            path_parts = url_parts[1].split('/', 1)
    	    if (len(path_parts) > 1):
	        self.port = int(path_parts[0])
	        self.service_path = path_parts[1]
 
    def make_connection(self, is_secure=False):
        return boto.connect_ec2(aws_access_key_id=self.ec2_user_access_key, 
			        aws_secret_access_key=self.ec2_user_secret_key,
				is_secure=is_secure,
				host=self.host,
				port=self.port,
				service=self.service_path)

