#!/usr/bin/env python

"""
    DSA demo and benchmark.

      Usage:  python -O dsa_bench.py [option option option ...]
        where options may include:
          makenewkey  showpubkey  showdigest  showprofile
          md5  sha1  sha256  sha512
          <key length>
    
    NB:
      DSA is formally defined with SHA-1 and key length 1024. 
      The OpenSSL implementation actually supports most any 
      hashing algorithm and key length, as long as the key
      length is longer than the digest length.  If not SHA-1
      and 1024, you should be very clear.  The use of "DSA"
      without any qualifiers implies SHA-1 and 1024.
    
    Larry Bugbee
    November 2006
    
    
    Some portions are Copyright (c) 1999-2003 Ng Pheng Siong. 
    All rights reserved.

    Portions created by Open Source Applications Foundation 
    (OSAF) are Copyright (C) 2004 OSAF. All Rights Reserved.

"""

from M2Crypto import DSA, EVP, Rand
from M2Crypto.EVP import MessageDigest
import sys, base64

# --------------------------------------------------------------
# program parameters

makenewkey  = 0     # 1 = make/save new key, 0 = use existing
showpubkey  = 0     # 1 = show the public key value
showdigest  = 0     # 1 = show the digest value
showprofile = 0     # 1 = use the python profiler

hashalgs = ['md5', 'ripemd160', 'sha1', 
            'sha224', 'sha256', 'sha384', 'sha512']

# default hashing algorithm
hashalg = 'sha1'

# default key length
keylen  = 1024

# number of speed test loops
N1 = N2 = 100

# --------------------------------------------------------------
# functions

def test(dsa, dgst):
    print '  testing signing and verification...',
    try:
        r,s = dsa.sign(dgst)
    except Exception, e:
        print '\n\n    *** %s *** \n' % e
        sys.exit()
    if not dsa.verify(dgst, r, s):
        print 'not ok'
    else:
        print 'ok'

def test_asn1(dsa, dgst):
    # XXX Randomly fails: bug in there somewhere... (0.9.4)
    print '  testing asn1 signing and verification...',
    blob = dsa.sign_asn1(dgst)
    if not dsa.verify_asn1(dgst, blob):
        print 'not ok'
    else:
        print 'ok'

def speed():
    from time import time
    t1 = time()
    for i in range(N1):
        r,s = dsa.sign(dgst)
    print '    %d signings:      %8.2fs' % (N1, (time() - t1))
    t1 = time()
    for i in range(N2):
        dsa.verify(dgst, r, s)
    print '    %d verifications: %8.2fs' % (N2, (time() - t1))
        
def test_speed(dsa, dgst):
    print '  measuring speed...'
    if showprofile:
        import profile
        profile.run('speed()')
    else:
        speed()
        print

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main(keylen, hashalg):
    global dsa, dgst     # this exists ONLY for speed testing
    
    Rand.load_file('randpool.dat', -1) 
        
    pvtkeyfilename = 'DSA%dpvtkey.pem' % (keylen)
    pubkeyfilename = 'DSA%dpubkey.pem' % (keylen)  
    
    if makenewkey:
        print '  making and saving a new key'
        dsa = DSA.gen_params(keylen)
        dsa.gen_key()
        dsa.save_key(pvtkeyfilename, None )  # no pswd callback
        dsa.save_pub_key(pubkeyfilename)
    else:
        print '  loading an existing key'
        dsa = DSA.load_key(pvtkeyfilename)
    print '  dsa key length:', len(dsa)
    
    if not dsa.check_key():
        raise 'key is not initialised'
        
    if showpubkey:
        dsa_pub = dsa.pub
        pub_pem = base64.encodestring(dsa_pub)
        print '  PEM public key is: \n',pub_pem

    # since we are testing signing and verification, let's not 
    # be fussy about the digest.  Just make one.
    md = EVP.MessageDigest(hashalg)
    md.update('can you spell subliminal channel?')
    dgst = md.digest()
    print '  hash algorithm: %s' % hashalg
    if showdigest:
        print '  %s digest: \n%s' % (hashalg, base64.encodestring(dgst))
    
    test(dsa, dgst)
#    test_asn1(dsa, dgst)
    test_speed(dsa, dgst)
    Rand.save_file('randpool.dat')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_usage():
    print """
  Usage:  python -O %s [option option option ...]
    where options may include:
      makenewkey  showpubkey  showdigest  showprofile
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
