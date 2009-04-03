#!/usr/bin/env python

"""DSA demonstration.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from M2Crypto import DSA, EVP, Rand

md=EVP.MessageDigest('sha1')
md.update('can you spell subliminal channel?')
dgst=md.digest()

d=DSA.load_key('dsatest.pem')

def test():
    print 'testing signing...',
    r,s=d.sign(dgst)
    if not d.verify(dgst, r, s):
        print 'not ok'
    else:
        print 'ok'

def test_asn1():
    # XXX Randomly fails: bug in there somewhere... (0.9.4)
    print 'testing asn1 signing...',
    blob=d.sign_asn1(dgst)
    if not d.verify_asn1(dgst, blob):
        print 'not ok'
    else:
        print 'ok'

def speed():
    from time import time
    N1 = 5242
    N2 = 2621
    t1 = time()
    for i in range(N1):
        r,s = d.sign(dgst)
    print '%d signings: %8.2fs' % (N1, (time() - t1))
    t1 = time()
    for i in range(N2):
        d.verify(dgst, r, s)
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

