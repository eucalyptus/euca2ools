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

import getopt
import sys
import os
import textwrap
import urlparse
import boto
import euca2ools
import euca2ools.utils
import euca2ools.exceptions
import euca2ools.nc.auth
import euca2ools.nc.connection
from boto.ec2.regioninfo import RegionInfo
from boto.s3.connection import OrdinaryCallingFormat
from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType
from boto.roboto.param import Param

SYSTEM_EUCARC_PATH = os.path.join('/etc', 'euca2ools', 'eucarc')

EC2RegionData = {
    'us-east-1' : 'ec2.us-east-1.amazonaws.com',
    'us-west-1' : 'ec2.us-west-1.amazonaws.com',
    'eu-west-1' : 'ec2.eu-west-1.amazonaws.com',
    'ap-southeast-1' : 'ec2.ap-southeast-1.amazonaws.com'}

import bdb
import traceback
try:
    import epdb as debugger
except ImportError:
    import pdb as debugger

def euca_except_hook(debugger_flag, debug_flag):
    def excepthook(typ, value, tb):
        if typ is bdb.BdbQuit:
            sys.exit(1)
        sys.excepthook = sys.__excepthook__

        if debugger_flag and sys.stdout.isatty() and sys.stdin.isatty():
            if debugger.__name__ == 'epdb':
                debugger.post_mortem(tb, typ, value)
            else:
                debugger.post_mortem(tb)
        elif debug_flag:
            print traceback.print_tb(tb)
            sys.exit(1)
        else:
            print value
            sys.exit(1)

    return excepthook

class EucaCommand(object):

    Description = 'Base class'
    StandardOptions = [Param(name='access_key',
                             short_name='a', long_name='access-key',
                             doc="User's Access Key ID.",
                             optional=True),
                       Param(name='secret_key',
                             short_name='s', long_name='secret-key',
                             doc="User's Secret Key.",
                             optional=True),
                       Param(name='config_path',
                             short_name=None, long_name='config',
                             doc="""Read credentials and cloud settings
                             from the specified config file (defaults to
                             $HOME/.eucarc or /etc/euca2ools/eucarc).""",
                             optional=True),
                       Param(short_name=None, long_name='debug',
                             doc='Turn on debugging output.',
                             optional=True, ptype='boolean'),
                       Param(short_name=None, long_name='debugger',
                             doc='Enable interactive debugger on error',
                             optional=True, ptype='boolean'),
                       Param(short_name='h', long_name='help',
                             doc='Display this help message.',
                             optional=True, ptype='boolean'),
                       Param(name='region_name',
                             short_name=None, long_name='region',
                             doc='region to direct requests to',
                             optional=True),
                       Param(short_name='U', long_name='url',
                             doc='URL of the Cloud to connect to.',
                             optional=True),
                       Param(short_name=None, long_name='version',
                             doc='Display the version of this tool.',
                             optional=True, ptype='boolean'),
                       Param(long_name='euca-auth',
                             doc='Use NC authentication mode',
                             optional=True, ptype='boolean')]
    Options = []
    Args = []
    Filters = []
    APIVersion = '2009-11-30'

    def __init__(self, is_euca=False, debug=False):
        self.access_key_short_name = '-a'
        self.secret_key_short_name = '-s'
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
        self.is_euca = is_euca
        self.euca_cert_path = None
        self.euca_private_key_path = None
        self.debug = 0
        self.debugger = False
        self.set_debug(debug)
        self.cmd_name = os.path.basename(sys.argv[0])
        self.setup_environ()
        self.check_for_conflict()
        self.process_cli_args()
        # h = NullHandler()
        # logging.getLogger('boto').addHandler(h)

    def set_debug(self, debug=False):
        if debug:
            boto.set_stream_logger('euca2ools')
            self.debug = 2

    def process_cli_args(self):
        (opts, args) = getopt.gnu_getopt(sys.argv[1:],
                                         self.short_options(),
                                         self.long_options())
        for (name, value) in opts:
            if name in ('-h', '--help'):
                self.usage()
                sys.exit()
            elif name == '--version':
                self.version()
            elif name == '--debug':
                self.set_debug(True)
            elif name == '--debugger':
                self.debugger = True
            elif name in (self.access_key_short_name, '--access-key'):
                self.ec2_user_access_key = value
            elif name in (self.secret_key_short_name, '--secret-key'):
                self.ec2_user_secret_key = value
            elif name in ('-U', '--url'):
                self.url = value
            elif name == '--region':
                self.region_name = value
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
            else:
                option = self.find_option(name)
                if option:
                    try:
                        value = option.convert(value)
                    except:
                        msg = '%s should be of type %s' % (option.long_name,
                                                           option.ptype)
                        self.display_error_and_exit(msg)
                    if option.cardinality in ('*', '+'):
                        if not hasattr(self, option.name):
                            setattr(self, option.name, [])
                        getattr(self, option.name).append(value)
                    else:
                        setattr(self, option.name, value)
        self.handle_defaults()
        self.check_required_options()

        for arg in self.Args:
            if not arg.optional and len(args)==0:
                self.usage()
                msg = 'Argument (%s) was not provided' % arg.name
                self.display_error_and_exit(msg)
            if arg.cardinality in ('*', '+'):
                setattr(self, arg.name, args)
            elif arg.cardinality == 1:
                if len(args) == 0 and arg.optional:
                    continue
                try:
                    value = arg.convert(args[0])
                except:
                    msg = '%s should be of type %s' % (arg.name,
                                                       arg.ptype)
                setattr(self, arg.name, value)
                if len(args) > 1:
                    msg = 'Only 1 argument (%s) permitted' % arg.name
                    self.display_error_and_exit(msg)

        sys.excepthook = euca_except_hook(self.debugger, self.debug)


    def check_for_conflict(self):
        for option in self.Options:
            if option.short_name == 'a' or option.short_name == 's':
                self.access_key_short_name = '-A'
                self.secret_key_short_name = '-S'
                opt = self.find_option('--access-key')
                opt.short_name = 'A'
                opt = self.find_option('--secret-key')
                opt.short_name = 'A'

    def find_option(self, op_name):
        for option in self.StandardOptions+self.Options:
            if option.synopsis_short_name == op_name or option.synopsis_long_name == op_name:
                return option
        return None

    def short_options(self):
        s = ''
        for option in self.StandardOptions + self.Options:
            if option.short_name:
                s += option.getopt_short_name
        return s

    def long_options(self):
        l = []
        for option in self.StandardOptions+self.Options:
            if option.long_name:
                l.append(option.getopt_long_name)
        if self.Filters:
            l.append('filter=')
        return l

    def required(self):
        return [ opt for opt in self.StandardOptions+self.Options if not opt.optional ]

    def required_args(self):
        return [ arg for arg in self.Args if not arg.optional ]

    def optional(self):
        return [ opt for opt in self.StandardOptions+self.Options if opt.optional ]

    def optional_args(self):
        return [ arg for arg in self.Args if arg.optional ]

    def handle_defaults(self):
        for option in self.Options+self.Args:
            if not hasattr(self, option.name):
                value = option.default
                if value is None and option.cardinality in ('+', '*'):
                    value = []
                elif value is None and option.ptype == 'boolean':
                    value = False
                elif value is None and option.ptype == 'integer':
                    value = 0
                setattr(self, option.name, value)

    def check_required_options(self):
        missing = []
        for option in self.required():
            if not hasattr(self, option.name) or getattr(self, option.name) is None:
                missing.append(option.long_name)
        if missing:
            msg = 'These required options are missing: %s' % ','.join(missing)
            self.display_error_and_exit(msg)

    def version(self):
        print '\tVersion: %s (BSD)' % euca2ools.__version__
        sys.exit(0)

    def param_usage(self, plist, label, n=30):
        nn = 80 - n - 4
        if plist:
            print '\n%s' % label
            for opt in plist:
                names = []
                if opt.short_name:
                    names.append(opt.synopsis_short_name)
                if opt.long_name:
                    names.append(opt.synopsis_long_name)
                if not names:
                    names.append(opt.name)
                doc = textwrap.dedent(opt.doc)
                doclines = textwrap.wrap(doc, nn)
                if doclines:
                    print '    %s%s' % (','.join(names).ljust(n), doclines[0])
                    for line in doclines[1:]:
                        print '%s%s' % (' '*(n+4), line)

    def filter_usage(self, n=30):
        if self.Filters:
            nn = 80 - n - 4
            print '\nAVAILABLE FILTERS'
            for filter in self.Filters:
                doc = textwrap.dedent(filter.doc)
                doclines = textwrap.wrap(doc, nn, fix_sentence_endings=True)
                print '    %s%s' % (filter.name.ljust(n), doclines[0])
                for line in doclines[1:]:
                    print '%s%s' % (' '*(n+4), line)
                

    def option_synopsis(self, options):
        s = ''
        for option in options:
            names = []
            if option.short_name:
                names.append(option.synopsis_short_name)
            if option.long_name:
                names.append(option.synopsis_long_name)
            if option.optional:
                s += '['
            s += ', '.join(names)
            if option.ptype != 'boolean':
                if option.metavar:
                    n = option.metavar
                elif option.name:
                    n = option.name
                else:
                    n = option.long_name
                s += ' <%s> ' % n
            if option.optional:
                s += ']'
        return s

    def synopsis(self):
        s = '%s ' % self.cmd_name
        n = len(s) + 1
        t = ''
        t += self.option_synopsis(self.required())
        t += self.option_synopsis(self.optional())
        if self.Filters:
            t += ' [--filter name=value]'
        if self.Args:
            t += ' '
            arg_names = []
            for arg in self.Args:
                name = arg.name
                if arg.optional:
                    name = '[ %s ]' % name
                arg_names.append(name)
            t += ' '.join(arg_names)
        lines = textwrap.wrap(t, 80-n)
        print s, lines[0]
        for line in lines[1:]:
            print '%s%s' % (' '*n, line)
                
    def usage(self):
        print '%s\n' % self.Description
        self.synopsis()
        self.param_usage(self.required()+self.required_args(),
                         'REQUIRED PARAMETERS')
        self.param_usage(self.optional()+self.optional_args(),
                         'OPTIONAL PARAMETERS')
        self.filter_usage()

    def display_error_and_exit(self, exc):
        try:
            print '%s: %s' % (exc.error_code, exc.error_message)
        except:
            print '%s' % exc
        finally:
            sys.exit(1)
            
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
            euca2ools.utils.parse_config(read_config, self.environ, envlist)
        else:
            for v in envlist:
                self.environ[v] = os.getenv(v)

    def get_environ(self, name):
        if self.environ.has_key(name):
            value = self.environ[name]
            if value:
                return self.environ[name]
        msg = 'Environment variable: %s not found' % name
        self.display_error_and_exit(msg)

    def get_credentials(self):
        if self.is_euca:
            if not self.euca_cert_path:
                self.euca_cert_path = self.environ['EUCA_CERT']
                if not self.euca_cert_path:
                    print 'EUCA_CERT variable must be set.'
                    raise euca2ools.exceptions.ConnectionFailed
            if not self.euca_private_key_path:
                self.euca_private_key_path = self.environ['EUCA_PRIVATE_KEY']
                if not self.euca_private_key_path:
                    print 'EUCA_PRIVATE_KEY variable must be set.'
                    raise euca2ools.exceptions.ConnectionFailed
        if not self.ec2_user_access_key:
            self.ec2_user_access_key = self.environ['EC2_ACCESS_KEY']
            if not self.ec2_user_access_key:
                print 'EC2_ACCESS_KEY environment variable must be set.'
                raise euca2ools.exceptions.ConnectionFailed

        if not self.ec2_user_secret_key:
            self.ec2_user_secret_key = self.environ['EC2_SECRET_KEY']
            if not self.ec2_user_secret_key:
                print 'EC2_SECRET_KEY environment variable must be set.'
                raise euca2ools.exceptions.ConnectionFailed

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

        if self.is_euca:
            return euca2ools.nc.connection.EucaConnection(
                private_key_path=self.euca_private_key_path,
                cert_path=self.euca_cert_path,
                aws_access_key_id=self.ec2_user_access_key,
                aws_secret_access_key=self.ec2_user_secret_key,
                is_secure=self.is_secure, debug=self.debug,
                host=self.host,
                port=self.port,
                path=self.service_path)
        else:
            return boto.connect_s3(
                aws_access_key_id=self.ec2_user_access_key,
                aws_secret_access_key=self.ec2_user_secret_key,
                is_secure=self.is_secure, debug=self.debug,
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
                                path=self.service_path,
                                api_version=self.APIVersion)
    
    def make_connection(self, conn_type='ec2'):
        self.get_credentials()
        if conn_type == 's3':
            conn = self.make_s3_connection()
        elif conn_type == 'ec2':
            conn = self.make_ec2_connection()
        else:
            conn = None
        return conn

    def make_connection_cli(self, conn_type='ec2'):
        """
        This just wraps up the make_connection call with appropriate
        try/except logic to print out an error message and exit if
        a EucaError is encountered.  This keeps the try/except logic
        out of all the command files.
        """
        try:
            conn = self.make_connection(conn_type)
            if not conn:
                msg = 'Unknown connection type: %s' % conn_type
                self.display_error_and_exit(msg)
            return conn
        except euca2ools.exceptions.EucaError, ex:
            self.display_error_and_exit(ex)

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
        except Exception, ex:
            self.display_error_and_exit(ex)

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
                    try:
                        block_dev_type.size = int(value_parts[1])
                    except ValueError:
                        pass
                if len(value_parts) > 2:
                    if value_parts[2] == 'true':
                        block_dev_type.delete_on_termination = True
                block_device_map[device_name] = block_dev_type
        return block_device_map

