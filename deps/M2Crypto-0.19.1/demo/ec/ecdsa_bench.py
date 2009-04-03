#!/usr/bin/env python

"""
    ECDSA demo and benchmark.

      Usage:  python -O ecdsa_bench.py [option option option ...]
        where options may include:
          makenewkey  showpubkey  showdigest  showprofile
          md5  sha1  sha256  sha512
          secp160r1  secp224r1  secp192k1  sect283r1
          sect283k1  secp256k1  secp384r1  secp521r1
        (other curves and hashes are supported, see below)

    Larry Bugbee, June 2006
    
    Portions:
      Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved.
      Copyright (c) 2005 Vrije Universiteit Amsterdam. All rights reserved.
    
"""

from M2Crypto import EC, EVP, Rand
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
        
curves   = ['secp112r1',
            'secp112r2',
            'secp128r1',
            'secp128r2',
            'secp160k1',
            'secp160r1',
            'secp160r2',
            'secp192k1',
            'secp224k1',
            'secp224r1',
            'secp256k1',
            'secp384r1',
            'secp521r1',
            'sect113r1',
            'sect113r2',
            'sect131r1',
            'sect131r2',
            'sect163k1',
            'sect163r1',
            'sect163r2',
            'sect193r1',
            'sect193r2',
            'sect233k1',
            'sect233r1',
            'sect239k1',
            'sect283k1',
            'sect283r1',
            'sect409k1',
            'sect409r1',
            'sect571k1',
            'sect571r1',
            'X9_62_prime192v1',
            'X9_62_prime192v2',
            'X9_62_prime192v3',
            'X9_62_prime239v1',
            'X9_62_prime239v2',
            'X9_62_prime239v3',
            'X9_62_prime256v1',
            'X9_62_c2pnb163v1',
            'X9_62_c2pnb163v2',
            'X9_62_c2pnb163v3',
            'X9_62_c2pnb176v1',
            'X9_62_c2tnb191v1',
            'X9_62_c2tnb191v2',
            'X9_62_c2tnb191v3',
            'X9_62_c2pnb208w1',
            'X9_62_c2tnb239v1',
            'X9_62_c2tnb239v2',
            'X9_62_c2tnb239v3',
            'X9_62_c2pnb272w1',
            'X9_62_c2pnb304w1',
            'X9_62_c2tnb359v1',
            'X9_62_c2pnb368w1',
            'X9_62_c2tnb431r1',
            'wap_wsg_idm_ecid_wtls1',
            'wap_wsg_idm_ecid_wtls3',
            'wap_wsg_idm_ecid_wtls4',
            'wap_wsg_idm_ecid_wtls5',
            'wap_wsg_idm_ecid_wtls6',
            'wap_wsg_idm_ecid_wtls7',
            'wap_wsg_idm_ecid_wtls8',
            'wap_wsg_idm_ecid_wtls9',
            'wap_wsg_idm_ecid_wtls10',
            'wap_wsg_idm_ecid_wtls11',
            'wap_wsg_idm_ecid_wtls12',
           ]

# The following two curves, according to OpenSSL, have a 
# "Questionable extension field!" and are not supported by 
# the OpenSSL inverse function.  ECError: no inverse.
# As such they cannot be used for signing.  They might, 
# however, be usable for encryption but that has not 
# been tested.  Until thir usefulness can be established,
# they are not supported at this time.
#
#      Oakley-EC2N-3: 
#        IPSec/IKE/Oakley curve #3 over a 155 bit binary field.
#      Oakley-EC2N-4: 
#        IPSec/IKE/Oakley curve #4 over a 185 bit binary field.
#
#      aka 'ipsec3' and 'ipsec4'

# curves2 is a shorthand convenience so as to not require the
# entering the "X9_62_" prefix
curves2  = ['prime192v1',
            'prime192v2',
            'prime192v3',
            'prime239v1',
            'prime239v2',
            'prime239v3',
            'prime256v1',
            'c2pnb163v1',
            'c2pnb163v2',
            'c2pnb163v3',
            'c2pnb176v1',
            'c2tnb191v1',
            'c2tnb191v2',
            'c2tnb191v3',
            'c2pnb208w1',
            'c2tnb239v1',
            'c2tnb239v2',
            'c2tnb239v3',
            'c2pnb272w1',
            'c2pnb304w1',
            'c2tnb359v1',
            'c2pnb368w1',
            'c2tnb431r1',
           ]

# default hashing algorithm
hashalg = 'sha1'

# default elliptical curve
curve   = 'secp160r1'    

# for a complete list of supported algorithms and curves, see 
# the bottom of this file

# number of speed test loops
N1 = N2 = 100

# --------------------------------------------------------------
# functions

def test(ec, dgst):
    print '  testing signing and verification...',
    try:
#        ec = EC.gen_params(EC.NID_secp160r1)
#        ec.gen_key()
        r,s = ec.sign_dsa(dgst)
    except Exception, e:
        print '\n\n    *** %s *** \n' % e
        sys.exit()
    if not ec.verify_dsa(dgst, r, s):
        print 'not ok'
    else:
        print 'ok'

def test_asn1(ec, dgst):
    print '  testing asn1 signing and verification...',
    blob = ec.sign_dsa_asn1(dgst)
    if not ec.verify_dsa_asn1(dgst, blob):
        print 'not ok'
    else:
        print 'ok'

def speed():
    from time import time
    t1 = time()
    for i in range(N1):
        r,s = ec.sign_dsa(dgst)
    print '    %d signings:      %8.2fs' % (N1, (time() - t1))
    t1 = time()
    for i in range(N2):
        ec.verify_dsa(dgst, r, s)
    print '    %d verifications: %8.2fs' % (N2, (time() - t1))
        
def test_speed(ec, dgst):
    print '  measuring speed...'
    if showprofile:
        import profile
        profile.run('speed()')
    else:
        speed()
        print

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main(curve, hashalg):
    global ec, dgst     # this exists ONLY for speed testing
    
    Rand.load_file('randpool.dat', -1) 
    
    if curve in curves2:
        curve = 'X9_62_' + curve
    ec_curve = eval('EC.NID_%s' % curve)
    
    pvtkeyfilename = '%spvtkey.pem' % (curve)
    pubkeyfilename = '%spubkey.pem' % (curve)  
    
    if makenewkey:
        print '  making and saving a new key'
        ec = EC.gen_params(ec_curve)
        ec.gen_key()
        ec.save_key(pvtkeyfilename, None )
        ec.save_pub_key(pubkeyfilename)
    else:
        print '  loading an existing key'
        ec=EC.load_key(pvtkeyfilename)
    print '  ecdsa key length:', len(ec)
    print '  curve: %s' % curve
    
    if not ec.check_key():
        raise 'key is not initialised'
        
    if showpubkey:
        ec_pub = ec.pub()
        pub_der = ec_pub.get_der()
        pub_pem = base64.encodestring(pub_der)
        print '  PEM public key is: \n',pub_pem

    # since we are testing signing and verification, let's not 
    # be fussy about the digest.  Just make one.
    md = EVP.MessageDigest(hashalg)
    md.update('can you spell subliminal channel?')
    dgst = md.digest()
    print '  hash algorithm: %s' % hashalg
    if showdigest:
        print '  %s digest: \n%s' % (base64.encodestring(dgst))
    
    test(ec, dgst)
#    test_asn1(ec, dgst)
    test_speed(ec, dgst)
    Rand.save_file('randpool.dat')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_usage():
    print """
  Usage:  python -O %s [option option option ...]
    where options may include:
      makenewkey  showpubkey  showdigest  showprofile
      md5  sha1  sha256  sha512
      secp160r1  secp224r1  secp192k1  sect283r1
      sect283k1  secp256k1  secp384r1  secp521r1
    (other curves and hashes are supported, check pgm src)
""" % sys.argv[0]
    sys.exit()

# --------------------------------------------------------------
# --------------------------------------------------------------

if __name__=='__main__':
    for arg in sys.argv[1:]:
        if arg in hashalgs:         hashalg = arg; continue
        if arg in curves + curves2: curve   = arg; continue
        if arg == 'makenewkey':   makenewkey  = 1; continue
        if arg == 'showpubkey':   showpubkey  = 1; continue
        if arg == 'showdigest':   showdigest  = 1; continue
        if arg == 'showprofile':  showprofile = 1; continue
        
        print '\n  *** argument "%s" not understood ***' % arg
        print_usage()
        
    main(curve, hashalg)


# --------------------------------------------------------------
# --------------------------------------------------------------
# --------------------------------------------------------------


"""
        Elliptical curves supported by OpenSSL
        ======================================

$ openssl ecparam -list_curves                              
  secp112r1 : SECG/WTLS curve over a 112 bit prime field
  secp112r2 : SECG curve over a 112 bit prime field
  secp128r1 : SECG curve over a 128 bit prime field
  secp128r2 : SECG curve over a 128 bit prime field
  secp160k1 : SECG curve over a 160 bit prime field
  secp160r1 : SECG curve over a 160 bit prime field
  secp160r2 : SECG/WTLS curve over a 160 bit prime field
  secp192k1 : SECG curve over a 192 bit prime field
  secp224k1 : SECG curve over a 224 bit prime field
  secp224r1 : NIST/SECG curve over a 224 bit prime field
  secp256k1 : SECG curve over a 256 bit prime field
  secp384r1 : NIST/SECG curve over a 384 bit prime field
  secp521r1 : NIST/SECG curve over a 521 bit prime field
  prime192v1: NIST/X9.62/SECG curve over a 192 bit prime field
  prime192v2: X9.62 curve over a 192 bit prime field
  prime192v3: X9.62 curve over a 192 bit prime field
  prime239v1: X9.62 curve over a 239 bit prime field
  prime239v2: X9.62 curve over a 239 bit prime field
  prime239v3: X9.62 curve over a 239 bit prime field
  prime256v1: X9.62/SECG curve over a 256 bit prime field
  sect113r1 : SECG curve over a 113 bit binary field
  sect113r2 : SECG curve over a 113 bit binary field
  sect131r1 : SECG/WTLS curve over a 131 bit binary field
  sect131r2 : SECG curve over a 131 bit binary field
  sect163k1 : NIST/SECG/WTLS curve over a 163 bit binary field
  sect163r1 : SECG curve over a 163 bit binary field
  sect163r2 : NIST/SECG curve over a 163 bit binary field
  sect193r1 : SECG curve over a 193 bit binary field
  sect193r2 : SECG curve over a 193 bit binary field
  sect233k1 : NIST/SECG/WTLS curve over a 233 bit binary field
  sect233r1 : NIST/SECG/WTLS curve over a 233 bit binary field
  sect239k1 : SECG curve over a 239 bit binary field
  sect283k1 : NIST/SECG curve over a 283 bit binary field
  sect283r1 : NIST/SECG curve over a 283 bit binary field
  sect409k1 : NIST/SECG curve over a 409 bit binary field
  sect409r1 : NIST/SECG curve over a 409 bit binary field
  sect571k1 : NIST/SECG curve over a 571 bit binary field
  sect571r1 : NIST/SECG curve over a 571 bit binary field
  c2pnb163v1: X9.62 curve over a 163 bit binary field
  c2pnb163v2: X9.62 curve over a 163 bit binary field
  c2pnb163v3: X9.62 curve over a 163 bit binary field
  c2pnb176v1: X9.62 curve over a 176 bit binary field
  c2tnb191v1: X9.62 curve over a 191 bit binary field
  c2tnb191v2: X9.62 curve over a 191 bit binary field
  c2tnb191v3: X9.62 curve over a 191 bit binary field
  c2pnb208w1: X9.62 curve over a 208 bit binary field
  c2tnb239v1: X9.62 curve over a 239 bit binary field
  c2tnb239v2: X9.62 curve over a 239 bit binary field
  c2tnb239v3: X9.62 curve over a 239 bit binary field
  c2pnb272w1: X9.62 curve over a 272 bit binary field
  c2pnb304w1: X9.62 curve over a 304 bit binary field
  c2tnb359v1: X9.62 curve over a 359 bit binary field
  c2pnb368w1: X9.62 curve over a 368 bit binary field
  c2tnb431r1: X9.62 curve over a 431 bit binary field
  wap-wsg-idm-ecid-wtls1: WTLS curve over a 113 bit binary field
  wap-wsg-idm-ecid-wtls3: NIST/SECG/WTLS curve over a 163 bit binary field
  wap-wsg-idm-ecid-wtls4: SECG curve over a 113 bit binary field
  wap-wsg-idm-ecid-wtls5: X9.62 curve over a 163 bit binary field
  wap-wsg-idm-ecid-wtls6: SECG/WTLS curve over a 112 bit prime field
  wap-wsg-idm-ecid-wtls7: SECG/WTLS curve over a 160 bit prime field
  wap-wsg-idm-ecid-wtls8: WTLS curve over a 112 bit prime field
  wap-wsg-idm-ecid-wtls9: WTLS curve over a 160 bit prime field
  wap-wsg-idm-ecid-wtls10: NIST/SECG/WTLS curve over a 233 bit binary field
  wap-wsg-idm-ecid-wtls11: NIST/SECG/WTLS curve over a 233 bit binary field
  wap-wsg-idm-ecid-wtls12: WTLS curvs over a 224 bit prime field
          Oakley-EC2N-3: 
                IPSec/IKE/Oakley curve #3 over a 155 bit binary field.
                Not suitable for ECDSA.
                Questionable extension field!
          Oakley-EC2N-4: 
                IPSec/IKE/Oakley curve #4 over a 185 bit binary field.
                Not suitable for ECDSA.
                Questionable extension field!

"""
