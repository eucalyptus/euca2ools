#!/usr/bin/env python
############################################################################
# Matt Rodriguez, LBNL MKRodriguez@lbl.gov
############################################################################ 
"""
Script that destroys a proxy certificate file by overwriting its contents
before the file is removed
""" 

import proxylib
import optparse, os 

USAGEHELP = "proxy_destroy.py file1 file2  Destroys files listed"
JUNK = "LalalAlalaLalalALalalAlalaLalalALalalAlalaLalalALalalAlalaLalalA"

def scrub_file(filename):
    """
    Overwrite the file with junk, before removing it
    """
    s = os.stat(filename)
    proxy_file = file(filename, "w") 
    size = s.st_size 
    while size > 64: 
        proxy_file.write(JUNK)
        size -= 64
    
    proxy_file.flush()
    proxy_file.close()
    os.remove(filename) 


def main():
    parser = optparse.OptionParser() 
    parser.set_usage(USAGEHELP)
    opts, args = parser.parse_args() 
    if len(args) is 0:
        proxy_file = proxylib.get_proxy_filename() 
        scrub_file(proxy_file) 
    
    for proxy_file in args:
        scrub_file(proxy_file)

if __name__ == "__main__": main()
