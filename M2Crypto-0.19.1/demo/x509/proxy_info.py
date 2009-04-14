#!/usr/bin/env python
############################################################################
# Matt Rodriguez, LBNL MKRodriguez@lbl.gov
############################################################################ 
"""
script that displays information about a proxy certificate
"""


import proxylib
import time, datetime, calendar
import sys, optparse

FILEHELP = "Location of the proxy."

def print_info(proxy_cert):
    """
    Print information about the proxy cert
    """
    cert = proxy_cert.getcert()
    print "Subject: ", cert.get_subject().as_text()
    print "Issuer: ", cert.get_issuer().as_text()
    pubkey = cert.get_pubkey() 
    size =  pubkey.size()
    print "Strength: ", size * 8 
    after = cert.get_not_after()
    after_tuple = time.strptime(str(after),"%b  %d %H:%M:%S %Y %Z") 
    expires = calendar.timegm(after_tuple)
    now = datetime.timedelta(seconds=time.time()) 
    expires = datetime.timedelta(seconds=expires) 
    td = expires - now 
    if td.days < 0:
        print "Time left: Proxy has expired."
    else: 
        hours = td.seconds / 3600 
        hours += td.days * 24 
        minutes = (td.seconds % 3600) / 60
        seconds =  (td.seconds % 3600) % 60
        print "Time left: %d:%d:%d" % (hours, minutes, seconds) 
        fraction = round((float(td.seconds) / float(3600 * 24)), 1) 
        print "Days left: ", str(td.days) + str(fraction)[1:]      
     
   
def main(): 
    parser = optparse.OptionParser()
    parser.add_option("-f", "--file", dest="filename", help=FILEHELP)
    (opts, args) = parser.parse_args()
    filename = opts.filename 
    if filename is None:   
        proxyfile = proxylib.get_proxy_filename()
    else:
        proxyfile = filename
    proxy_cert = proxylib.Proxy()
    try:
        proxy_cert.read(proxyfile)
    except IOError:
        print "The file: " + proxyfile + " does not exist."
        sys.exit(0)
    print_info(proxy_cert)

if __name__ == "__main__": main()
