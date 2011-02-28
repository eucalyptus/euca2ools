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

import euca2ools
import exceptions
import validate
import boto
import getopt
import sys
import os
import subprocess
import urlparse
from boto.ec2.regioninfo import RegionInfo
from boto.ec2.blockdevicemapping import BlockDeviceMapping
from boto.ec2.blockdevicemapping import BlockDeviceType
from boto.s3.connection import OrdinaryCallingFormat
import logging

SYSTEM_EUCARC_PATH = os.path.join('/etc', 'euca2ools', 'eucarc')

USAGE = \
"""
-a, --access-key		User's Access Key ID.

-s, --secret-key		User's Secret Key.

--region			region to describe availability zones for

-U, --url			URL of the Cloud to connect to.

--config			Read credentials and cloud settings from the 
				specified config file (defaults to
                                $HOME/.eucarc or /etc/euca2ools/eucarc).

-h, --help			Display this help message.

--version 			Display the version of this tool.

--debug 			Turn on debugging.

--euca-auth                     Use Euca component authentication.

Euca2ools will use the environment variables EC2_URL, EC2_ACCESS_KEY, EC2_SECRET_KEY, EC2_CERT, EC2_PRIVATE_KEY, S3_URL, EUCALYPTUS_CERT by default.
"""

EC2RegionData = {
    'us-east-1' : 'ec2.us-east-1.amazonaws.com',
    'us-west-1' : 'ec2.us-west-1.amazonaws.com',
    'eu-west-1' : 'ec2.eu-west-1.amazonaws.com',
    'ap-southeast-1' : 'ec2.ap-southeast-1.amazonaws.com'}

class NullHandler(logging.Handler):

    def emit(self, record):
        pass

class Controller(object):

    def __init__(self, short_opts=None, long_opts=None,
                 is_s3=False, is_euca=False, compat=False,
                 cmd_usage=None):
        self.ec2_user_access_key = None
        self.ec2_user_secret_key = None
        self.url = None
        self.filters = {}
        self.region_name = None
        self.region = RegionInfo()
        self.config_file_path = None
        self.is_secure = True
        self.port = 443
        self.service_path = '/'
        self.is_s3 = is_s3
        self.is_euca = is_euca
        self.cmd_usage = cmd_usage
        self.euca_cert_path = None
        self.euca_private_key_path = None
        if compat:
            self.secret_key_opt = 'S'
            self.access_key_opt = 'A'
        else:
            self.secret_key_opt = 's'
            self.access_key_opt = 'a'
        if not short_opts:
            short_opts = ''
        if not long_opts:
            long_opts = []
        short_opts += 'hU:'
        short_opts += '%s:' % self.secret_key_opt
        short_opts += '%s:' % self.access_key_opt
        long_opts += ['access-key=', 'secret-key=', 'url=', 'help',
                      'version', 'debug', 'config=', 'euca-auth',
                      'region=', 'filter=']
        (opts, args) = getopt.gnu_getopt(sys.argv[1:], short_opts,
                long_opts)
        self.opts = opts
        self.args = args
        self.debug = False
        for (name, value) in opts:
            if name in ('-h', '--help'):
                self.usage(cmd_usage=self.cmd_usage, status=0)
            elif name == '--version':
                self.version()
            elif name in ('-%s' % self.access_key_opt, '--access-key'):
                self.ec2_user_access_key = value
            elif name in ('-%s' % self.secret_key_opt, '--secret-key'):
                try:
                    self.ec2_user_secret_key = int(value)
                    self.ec2_user_secret_key = None
                except ValueError:
                    self.ec2_user_secret_key = value
            elif name in ('-U', '--url'):
                self.url = value
            elif name == '--region':
                self.region_name = value
            elif name == '--debug':
                boto.set_stream_logger('euca2ools')
                self.debug = 2
            elif name == '--config':
                self.config_file_path = value
            elif name == '--euca-auth':
                self.is_euca = True
            elif name == '--filter':
                try:
                    name, value = value.split('=')
                except ValueError:
                    msg = 'Filters must be of the form name=value'
                    self.display_error_and_exit(msg)
                self.filters[name] = value
        self.setup_environ()

        h = NullHandler()
        logging.getLogger('boto').addHandler(h)

    def version(self):
        print '\tVersion: %s (BSD)' % euca2ools.__version__
        sys.exit(0)

    def display_tools_version(self):
        print '\t%s %s' % (euca2ools.__tools_version__,
                           euca2ools.__api_version__)

    def usage(self, compat=False, cmd_usage=None, status=1):
        if compat:
            usage = USAGE.replace('-s,', '-S,')
            usage = usage.replace('-a,', '-A,')
        else:
            usage = USAGE
        if cmd_usage:
            print cmd_usage
        print usage
        sys.exit(status)

    def display_error_and_exit(self, exc):
        try:
            print '%s: %s' % (exc.error_code, exc.error_message)
        except:
            print '%s' % exc
        finally:
            exit(1)
            
    def setup_environ(self):
        envlist = ('EC2_ACCESS_KEY', 'EC2_SECRET_KEY',
                   'S3_URL', 'EC2_URL', 'EC2_CERT', 'EC2_PRIVATE_KEY',
                   'EUCALYPTUS_CERT', 'EC2_USER_ID',
                   'EUCA_CERT', 'EUCA_PRIVATE_KEY')
        self.environ = {}
        user_eucarc = None
        if 'HOME' in os.environ:
            user_eucarc = os.path.join(os.getenv('HOME'), '.eucarc')
        read_config = False
        if self.config_file_path \
            and os.path.exists(self.config_file_path):
            read_config = self.config_file_path
        elif user_eucarc is not None and os.path.exists(user_eucarc):
            if os.path.isdir(user_eucarc):
                user_eucarc = os.path.join(user_eucarc, 'eucarc')
                if os.path.isfile(user_eucarc):
                    read_config = user_eucarc
            elif os.path.isfile(user_eucarc):
                read_config = user_eucarc
        elif os.path.exists(SYSTEM_EUCARC_PATH):
            read_config = SYSTEM_EUCARC_PATH
        if read_config:
            parse_config(read_config, self.environ, envlist)
        else:
            for v in envlist:
                self.environ[v] = os.getenv(v)

    def get_environ(self, name):
        if self.environ.has_key(name):
            return self.environ[name]
        else:
            print '%s not found' % name
            raise NotFoundError

    def get_credentials(self):
        if self.is_euca:
            if not self.euca_cert_path:
                self.euca_cert_path = self.environ['EUCA_CERT']
                if not self.euca_cert_path:
                    print 'EUCA_CERT variable must be set.'
                    raise exceptions.ConnectionFailed
            if not self.euca_private_key_path:
                self.euca_private_key_path = self.environ['EUCA_PRIVATE_KEY']
                if not self.euca_private_key_path:
                    print 'EUCA_PRIVATE_KEY variable must be set.'
                    raise exceptions.ConnectionFailed
        else:
            if not self.ec2_user_access_key:
                self.ec2_user_access_key = self.environ['EC2_ACCESS_KEY']
                if not self.ec2_user_access_key:
                    print 'EC2_ACCESS_KEY environment variable must be set.'
                    raise exceptions.ConnectionFailed

            if not self.ec2_user_secret_key:
                self.ec2_user_secret_key = self.environ['EC2_SECRET_KEY']
                if not self.ec2_user_secret_key:
                    print 'EC2_SECRET_KEY environment variable must be set.'
                    raise exceptions.ConnectionFailed

    def get_connection_details(self):
        self.port = None
        self.service_path = '/'
        
        rslt = urlparse.urlparse(self.url)
        if rslt.scheme == 'https':
            self.is_secure = True
        else:
            self.is_secure = False

        self.host = rslt.netloc
        l = self.host.split(':')
        if len(l) > 1:
            self.host = l[0]
            self.port = int(l[1])

        if rslt.path:
            self.service_path = rslt.path

    def make_s3_connection(self):
        if not self.url:
            self.url = self.environ['S3_URL']
            if not self.url:
                self.url = \
                    'http://localhost:8773/services/Walrus'
                print 'S3_URL not specified. Trying %s' \
                    % self.url

        self.get_connection_details()
        
        return boto.connect_s3(aws_access_key_id=self.ec2_user_access_key,
                               aws_secret_access_key=self.ec2_user_secret_key,
                               is_secure=self.is_secure,
                               host=self.host,
                               port=self.port,
                               calling_format=OrdinaryCallingFormat(),
                               path=self.service_path)

    def make_ec2_connection(self):
        if self.region_name:
            self.region.name = self.region_name
            try:
                self.region.endpoint = EC2RegionData[self.region_name]
            except KeyError:
                print 'Unknown region: %s' % self.region_name
                sys.exit(1)
        elif not self.url:
            self.url = self.environ['EC2_URL']
            if not self.url:
                self.url = \
                    'http://localhost:8773/services/Eucalyptus'
                print 'EC2_URL not specified. Trying %s' \
                    % self.url

        if not self.region.endpoint:
            self.get_connection_details()
            self.region.name = 'eucalyptus'
            self.region.endpoint = self.host

        return boto.connect_ec2(aws_access_key_id=self.ec2_user_access_key,
                                aws_secret_access_key=self.ec2_user_secret_key,
                                is_secure=self.is_secure,
                                debug=self.debug,
                                region=self.region,
                                port=self.port,
                                path=self.service_path)

    def make_nc_connection(self):
        self.port = None
        self.service_path = '/'
        
        rslt = urlparse.urlparse(self.url)
        if rslt.scheme == 'https':
            self.is_secure = True
        else:
            self.is_secure = False

        self.get_connection_details()
        
        # I'm importing these here because they depend
        # on a boto version > 2.0b3
        import admin.connection
        import admin.auth
        return admin.connection.EucaConnection(
            aws_access_key_id=self.ec2_user_access_key,
            aws_secret_access_key=self.ec2_user_secret_key,
            cert_path=self.euca_cert_path,
            private_key_path=self.euca_private_key_path,
            is_secure=self.is_secure,
            host=self.host,
            port=self.port,
            path=self.service_path)

    def make_connection(self):
        self.get_credentials()
        if self.is_euca:
            conn = self.make_nc_connection()
        elif self.is_s3:
            conn = self.make_s3_connection()
        else:
            conn = self.make_ec2_connection()
        return conn

    def make_connection_cli(self):
        """
        This just wraps up the make_connection call with appropriate
        try/except logic to print out an error message and exit if
        a EucaError is encountered.  This keeps the try/except logic
        out of all the command files.
        """
        try:
            return self.make_connection()
        except exceptions.EucaError as ex:
            print ex.message
            sys.exit(1)

    def make_request_cli(self, connection, request_name, **params):
        """
        This provides a simple
        This just wraps up the make_connection call with appropriate
        try/except logic to print out an error message and exit if
        a EucaError is encountered.  This keeps the try/except logic
        out of all the command files.
        """
        try:
            if self.filters:
                params['filters'] = self.filters
            method = getattr(connection, request_name)
        except AttributeError:
            print 'Unknown request: %s' % request_name
            sys.exit(1)
        try:
            return method(**params)
        except Exception as ex:
            self.display_error_and_exit(ex)

    def get_relative_filename(self, filename):
        return os.path.split(filename)[-1]

    def get_file_path(self, filename):
        relative_filename = self.get_relative_filename(filename)
        file_path = os.path.dirname(filename)
        if len(file_path) == 0:
            file_path = '.'
        return file_path

    #
    # These validate_* methods are called by the command line executables
    # and, as such, they should print an appropriate message and exit
    # when invalid input is detected.
    #
    def _try_validate(self, method, value, msg):
        try:
            method(value)
        except exceptions.ValidationError as ex:
            if msg:
                print msg
            else:
                print ex.message
            sys.exit(1)
            
    def validate_address(self, address, msg=None):
        self._try_validate(validate.validate_address, address, msg)

    def validate_instance_id(self, id, msg=None):
        self._try_validate(validate.validate_instance_id, id, msg)
            
    def validate_volume_id(self, id, msg=None):
        self._try_validate(validate.validate_volume_id, id, msg)

    def validate_volume_size(self, size, msg=None):
        self._try_validate(validate.validate_volume_size, size, msg)

    def validate_snapshot_id(self, id, msg=None):
        self._try_validate(validate.validate_snapshot_id, id, msg)

    def validate_protocol(self, proto, msg=None):
        self._try_validate(validate.validate_protocol, proto, msg)

    def validate_file(self, path, msg=None):
        self._try_validate(validate.validate_file, path, msg)

    def validate_dir(self, path, msg=None):
        self._try_validate(validate.validate_dir, path, msg)

    def validate_bundle_id(self, id, msg=None):
        self._try_validate(validate.validate_bundle_id, id, msg)

    def get_relative_filename(self, filename):
        return os.path.split(filename)[-1]

    def get_file_path(self, filename):
        relative_filename = self.get_relative_filename(filename)
        file_path = os.path.dirname(filename)
        if len(file_path) == 0:
            file_path = '.'
        return file_path

    def parse_block_device_args(self, block_device_maps_args):
        block_device_map = BlockDeviceMapping()
        for block_device_map_arg in block_device_maps_args:
            parts = block_device_map_arg.split('=')
            if len(parts) > 1:
                device_name = parts[0]
                block_dev_type = BlockDeviceType()
                value_parts = parts[1].split(':')
                if value_parts[0].startswith('snap'):
                    block_dev_type.snapshot_id = value_parts[0]
                else:
                    if value_parts[0].startswith('ephemeral'):
                        block_dev_type.ephemeral_name = value_parts[0]
                if len(value_parts) > 1:
                    block_dev_type.size = int(value_parts[1])
                if len(value_parts) > 2:
                    if value_parts[2] == 'true':
                        block_dev_type.delete_on_termination = True
                block_device_map[device_name] = block_dev_type
        return block_device_map

# read the config file 'config', update 'dict', setting
# the value from the config file for each element in array 'keylist'
# "config" is a bash syntax file defining bash variables


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

