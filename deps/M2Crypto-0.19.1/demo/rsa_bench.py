#!/usr/bin/env python

"""
    RSA signing demo and benchmark.

      Usage:  python -O rsa_bench.py [option option option ...]
        where options may include:
          makenewkey  showdigest  showprofile
          md5  sha1  sha256  sha512
          <key length>
        
    Larry Bugbee
    November 2006
    
    
    Some portions are Copyright (c) 1999-2003 Ng Pheng Siong. 
    All rights reserved.

    Portions created by Open Source Applications Foundation 
    (OSAF) are Copyright (C) 2004 OSAF. All Rights Reserved.

"""

from M2Crypto import RSA, EVP, Rand
from M2Crypto.EVP import MessageDigest
import sys, base64

# --------------------------------------------------------------
# program parameters

makenewkey  = 0     # 1 = make/save new key, 0 = use existing
showpubkey  = 0     # 1 = show the public key value
showdigest  = 0     # 1 = show the digest value
showprofile = 0     # 1 = use the python profiler

hashalgs  = ['md5', 'ripemd160', 'sha1', 
             'sha224', 'sha256', 'sha384', 'sha512']

# default hashing algorithm
hashalg  = 'sha1'

# default key parameters
keylen   = 1024
exponent = 65537
'''
  There is some temptation to use an RSA exponent of 3
  because 1) it is easy to remember and 2) it minimizes the
  effort of signature verification.  Unfortunately there 
  a couple of attacks based on the use of 3.  From a draft 
  RFC (Easklake, Dec 2000):
    A public exponent of 3 minimizes the effort needed to 
    verify a signature.  Use of 3 as the public exponent is
    weak for confidentiality uses since, if the same data 
    can be collected encrypted under three different keys 
    with an exponent of 3 then, using the Chinese Remainder 
    Theorem [NETSEC], the original plain text can be easily
    recovered.   
  This applies to confidentiality so it is not of major 
  concern here.  The second attack is a protocol implementation 
  weakness and can be patched, but has the patch been applied?  
  ...correctly?  It is arguably better to get into the habit 
  of using a stronger exponent and avoiding these and possible 
  future attacks based on 3.  I suggest getting in the habit 
  of using something stronger.  Some suggest using 65537.
'''

# number of speed test loops
N1 = N2  = 100

# --------------------------------------------------------------
# functions

def test(rsa, dgst):
    print '  testing signing and verification...',
    try:
        sig = rsa.sign(dgst)
    except Exception, e:
        print '\n\n    *** %s *** \n' % e
        sys.exit()
    if not rsa.verify(dgst, sig):
        print 'not ok'
    else:
        print 'ok'

def test_asn1(rsa, dgst):
    print '  testing asn1 signing and verification...',
    blob = rsa.sign_asn1(dgst)
    if not rsa.verify_asn1(dgst, blob):
        print 'not ok'
    else:
        print 'ok'

def speed():
    from time import time
    t1 = time()
    for i in range(N1):
        sig = rsa.sign(dgst)
    print '    %d signings:      %8.2fs' % (N1, (time() - t1))
    t1 = time()
    for i in range(N2):
        rsa.verify(dgst, sig)
    print '    %d verifications: %8.2fs' % (N2, (time() - t1))
        
def test_speed(rsa, dgst):
    print '  measuring speed...'
    if showprofile:
        import profile
        profile.run('speed()')
    else:
        speed()
        print

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main(keylen, hashalg):
    global rsa, dgst     # this exists ONLY for speed testing
    
    Rand.load_file('randpool.dat', -1) 
        
    pvtkeyfilename = 'rsa%dpvtkey.pem' % (keylen)
    pubkeyfilename = 'rsa%dpubkey.pem' % (keylen)  
    
    if makenewkey:
        print '  making and saving a new key'
        rsa = RSA.gen_key(keylen, exponent)
        rsa.save_key(pvtkeyfilename, None )  # no pswd callback
        rsa.save_pub_key(pubkeyfilename)
    else:
        print '  loading an existing key'
        rsa = RSA.load_key(pvtkeyfilename)
    print '  rsa key length:', len(rsa)
    
    if not rsa.check_key():
        raise 'key is not initialised'

    # since we are testing signing and verification, let's not 
    # be fussy about the digest.  Just make one.
    md = EVP.MessageDigest(hashalg)
    md.update('can you spell subliminal channel?')
    dgst = md.digest()
    print '  hash algorithm: %s' % hashalg
    if showdigest:
        print '  %s digest: \n%s' % (hashalg, base64.encodestring(dgst))
    
    test(rsa, dgst)
#    test_asn1(rsa, dgst)
    test_speed(rsa, dgst)
    Rand.save_file('randpool.dat')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_usage():
    print """
  Usage:  python -O %s [option option option ...]
    where options may include:
      makenewkey  showdigest  showprofile
      md5  sha1  sha256  sha512
      <key length>
""" % sys.argv[0]
    sys.exit()

# --------------------------------------------------------------
# --------------------------------------------------------------

if __name__=='__main__':
    for arg in sys.argv[1:]:
        if arg in hashalgs:         hashalg = arg; continue
        if arg == 'makenewkey':   makenewkey  = 1; continue
        if arg == 'showpubkey':   showpubkey  = 1; continue
        if arg == 'showdigest':   showdigest  = 1; continue
        if arg == 'showprofile':  showprofile = 1; continue
        try:
            keylen = int(arg)
        except:
            print '\n  *** argument "%s" not understood ***' % arg
            print_usage()
        
    main(keylen, hashalg)


# --------------------------------------------------------------
# --------------------------------------------------------------
# --------------------------------------------------------------
