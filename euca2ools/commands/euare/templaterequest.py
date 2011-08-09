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
"""
# Introduction

This module is an example of how to create a command line tool for
a new request/response.  Creating a new command line tool requires
two parts:

* A Request class (like this example one).  The request class
  describes the request parameters and, optionally, the response.
  It also includes a couple of boilerplate functions that are
  used in the wrapper script (see next bullet) and an optional
  method that formats the output of the request.

* A wrapper script.  This is an executable Python script that
  allows the Request to be used as a command line tool.  This
  script is very simple, consisting of only a couple of lines
  of Python.

With these two pieces, it is possible to create a command line
tool that will make the request to the remote service, receive
the response and then format the response for output to the
command shell.

The following import statements are required for any Request
class that represents a request against an IAM/Euare server.
"""

from boto.roboto.awsqueryrequest import AWSQueryRequest
from boto.roboto.param import Param
import euca2ools.commands.euare


class MyRequest(AWSQueryRequest):
    """
    ## The Request Class
    
    This class represents the actual request to the remote
    service.  By subclassing from AWSQueryRequest, most of
    the hard work is done for you although the AWSQueryRequest
    superclass only works if your service uses the AWS Query
    style API.  There are a few things that you need to remember:

    * The name of the class must be the name of the Request.
      So, if the over-the-wire request name or action is
      "NowAMiracleOccurs", then you class should be called
      NowAMiracleOccurs and it should be a subclass of
      AWSQueryRequest.

    * You can provide an optional Description class attribute.
      Currently this is not used but will probably be
      incorporated into the command line help that is
      generated automatically for your command.

    * You need to define a Param object for each parameter that
      your request accepts.  Each Param object has the following
      attributes:

      ** name - the actual name of the parameter in the request.

      ** short_name - (optional) the short, single-letter form
         of the command line option (e.g. -i)

      ** long_name - (optional) the long version of the
         command line option (--important-param)

      ** ptype - the type of parameter, defaults to
         string.  Possible types are:

         *** string
         *** integer
         *** boolean - signals that this is a flag option
         *** file - assumes value is a path to a file to read
         *** datetime

      ** optional - determines whether the parameter is
         optional or required, defaults to optional.

      ** doc - documentation that will be displayed when
         the user askes for help on the request (-h)

    """

    ServiceClass = euca2ools.commands.euare.Euare

    Name = 'MyRequest'
    Description = 'This is my new request.'
    Params = [
        Param(name='ImportantParam',
              short_name='i',
              long_name='important-param',
              ptype='string',
              optional=False,
              doc="""A really important parameter. """),
        Param(name='UnimportantParam',
              short_name='u',
              long_name='unimportant-param',
              ptype='string',
              optional=True,
              doc="""This param is not that important.""")
        ]

    def cli_formatter(self, data):
        """
        This method is called to generate the output for your
        command.  There is a generic version in the superclass
        that attempts to do something reasonable by correlating
        the response data to the description of the response but
        you will probably want to override this to get your
        desired output.

        This method is called with a dict-like data structure
        that contains all of the response data from the server.
        This implementation simply prints that entire data structure
        out but you can easily pick and choose what you want once
        you understand the output.
        """
        print 'Output from MyRequest:'
        print data

    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
