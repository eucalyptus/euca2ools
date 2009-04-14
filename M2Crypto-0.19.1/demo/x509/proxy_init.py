#!/usr/bin/env python
############################################################################
# Matt Rodriguez, LBNL  MKRodriguez@lbl.gov 
############################################################################ 
"""
script that generates a proxy certificate
"""

import proxylib 
import optparse 
import sys

OUTHELP = "Location of the new proxy cert."
CERTHELP = "Location of user certificate."
KEYHELP  = "Location of the user key."
VALIDHELP = "h:m Proxy certificate is valid for h hours and m minutes."
FULLPROXY = "Creates a limited proxy"
def main():
    parser = optparse.OptionParser()
    parser.add_option('-o', '--output', dest='output', help=OUTHELP)
    parser.add_option('-c', '--cert' , dest='cert', help=CERTHELP)
    parser.add_option('-k', '--key', dest='key', help=KEYHELP)
    parser.add_option('-v', '--valid', dest='valid', help=VALIDHELP)
    parser.add_option('-l', '--limited', action="store_true", 
                      default=False, dest='limited', help=VALIDHELP)
    (opts, args) = parser.parse_args()
    kw = {} 
    kw['cert'] = opts.cert
    kw['key'] = opts.key
    if opts.valid is None:
        valid_tuple = (12, 0)
    else:
        valid = opts.valid.split(':') 
        valid_tuple = tuple(map(int, valid))
    kw['valid'] = valid_tuple 
    kw['full'] = not opts.limited
    try:
        proxy_factory = proxylib.ProxyFactory(kw)
    except IOError:
        print "Can't find usercert or userkey. Use the -c or -k arguments"
        sys.exit(0)
    proxy_factory.generate()
    proxy_cert = proxy_factory.getproxy()
    if opts.output is None:
        proxy_cert.write(proxylib.get_proxy_filename())
    else:
        proxy_cert.write(opts.output)
    
if __name__ == "__main__": main()
