#!/usr/bin/env python

# Clean up M2Crypto source base.

import glob, os, os.path, sys

def zap(arg, dirname, names):
    for f in glob.glob(dirname + arg):
        try:
            os.remove(f)
        except:
            pass

if __name__ == "__main__":
    start = sys.argv[1]

    os.path.walk(start, zap, "/*.pyc")

    if os.name == 'nt':
        zap_m2 = ("__m2cryptoc.pyd","_m2crypto.py")
    elif os.name == 'posix':
        zap_m2 = ("__m2crypto.so","_m2crypto.py")
    for x in zap_m2:
        try:
            os.remove("%s/M2Crypto/%s" % (start, x))
        except:
            pass

    zap_swig = ("_m2crypto_wrap*", "_m2crypto.c", "_m2crypto.py", "vc60.pdb")
    for x in zap_swig:
        for z in glob.glob("%s/SWIG/%s" % (start, x)):
            try:
                os.remove(z)
            except:
                pass


