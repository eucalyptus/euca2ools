#!/usr/bin/env python

"""ECDSA demonstration.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved.
Portions copyright (c) 2005-2006 Vrije Universiteit Amsterdam. All rights reserved.
"""

from M2Crypto import EC, EVP, Rand
import base64

md=EVP.MessageDigest('sha1')
md.update('can you spell subliminal channel?')
dgst=md.digest()

ec=EC.load_key('ecdsatest.pem')
#ec=EC.gen_params(EC.NID_sect233k1)
#ec.gen_key()
ec_pub = ec.pub()
pub_der = ec_pub.get_der()
pub_pem = base64.encodestring(pub_der)
print 'PEM public key is',pub_pem
ec.save_key( 'ecdsatest.pem', None )


def test():
    print 'testing signing...',
    r,s=ec.sign_dsa(dgst)
    if not ec.verify_dsa(dgst, r, s):
        print 'not ok'
    else:
        print 'ok'

def test_asn1():
    # XXX Randomly fails: bug in there somewhere... (0.9.4)
    print 'testing asn1 signing...',
    blob=ec.sign_dsa_asn1(dgst)
    if not ec.verify_dsa_asn1(dgst, blob):
        print 'not ok'
    else:
        print 'ok'

def speed():
    from time import time
    N1 = 5242
    N2 = 2621
    t1 = time()
    for i in range(N1):
        r,s = ec.sign(dgst)
    print '%d signings: %8.2fs' % (N1, (time() - t1))
    t1 = time()
    for i in range(N2):
        ec.verify(dgst, r, s)
    print '%d verifications: %8.2fs' % (N2, (time() - t1))
        
def test_speed():
    print 'measuring speed...'
    import profile
    profile.run('speed()')


if __name__=='__main__':
    Rand.load_file('randpool.dat', -1) 
    test()
    test_asn1()
    #test_speed()
    Rand.save_file('randpool.dat')

