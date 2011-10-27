#!/usr/local/bin/python
# -*- coding: utf-8 -*-

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
# Author: David Kavanagh david.kavanagh@eucalyptus.com

import os
import urllib2
from boto.roboto.param import Param
from boto.roboto.awsqueryrequest import AWSQueryRequest
import euca2ools.commands.eustore

try:
    import simplejson as json
except ImportError:
    import json

class DescribeImages(AWSQueryRequest):

    ServiceClass = euca2ools.commands.eustore.Eustore

    Description = """lists images from Eucalyptus.com"""

    def fmtCol(self, value, width):
        valLen = len(value)
        if valLen > width:
            return value[0:width-2]+".."
        else:
            return value.ljust(width, ' ')

    def main(self):
        self.eustore_url = self.ServiceClass.StoreBaseURL
        if os.environ.has_key('EUSTORE_URL'):
            self.eustore_url = os.environ['EUSTORE_URL']
        catURL = self.eustore_url + "catalog.json"
        response = urllib2.urlopen(catURL).read()
        parsed_cat = json.loads(response)
        if len(parsed_cat) > 0:
            image_list = parsed_cat['images']
            for image in image_list:
                print self.fmtCol(image['name'],25)+image['description']
                print "    OS:"+self.fmtCol(image['os'],12)+ \
                      " Arch:"+self.fmtCol(image['architecture'],8)+ \
                      " Vers:"+self.fmtCol(image['version'],15)

    def main_cli(self):
        self.do_cli()

