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


import sys
from boto.roboto.awsqueryservice import AWSQueryService

class Eustore(AWSQueryService):

    Name = 'eustore'
    Description = 'Eucalyptus Image Store'
    APIVersion = '2011-01-01'
    Authentication = 'sign-v2'
    Path = '/'
    Port = 443
    Provider = 'aws'
    EnvURL = 'EC2_URL'

    StoreBaseURL = 'http://emis.eucalyptus.com/'
    EuStoreVersion = 'eustore-catalog-2011-12-29'
    RequestHeaders = {'User-Agent': 'euca2ools/eustore',
                      'eustore-version': EuStoreVersion}

class progressBar:
    def __init__(self, maxVal):
        self.maxVal=maxVal
        self.currVal=0
        print "0-----1-----2-----3-----4-----5-----6-----7-----8-----9-----10"
        self.progShowing=0

    def update(self, val):
        count=min(val, self.maxVal)
        progDone=62*count/self.maxVal
        if self.progShowing < progDone:
            for i in range(progDone - self.progShowing):
                sys.stdout.write("#")
            sys.stdout.flush()
            self.progShowing = progDone
        if progDone==62:
            sys.stdout.write("\n")
