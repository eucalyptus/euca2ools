#!/usr/bin/env python

"""RSA demonstration.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from M2Crypto import RSA, EVP, Rand

msg="The magic words are squeamish ossifrage."
sha1=EVP.MessageDigest('sha1')
sha1.update(msg)
dgst=sha1.digest()

priv=RSA.load_key('rsa.priv.pem')
pub=RSA.load_pub_key('rsa.pub.pem')

def test_encrypt(padding):
    print 'testing public-key encryption:', padding
    padding=eval('RSA.'+padding)
    ctxt=pub.public_encrypt(dgst, padding)
    ptxt=priv.private_decrypt(ctxt, padding)
    if ptxt!=dgst:
        print 'public_encrypt -> private_decrypt: not ok'

def test_sign(padding):
    print 'testing private-key signing:', padding
    padding=eval('RSA.'+padding)
    ctxt=priv.private_encrypt(dgst, padding)    
    ptxt=pub.public_decrypt(ctxt, padding)
    if ptxt!=dgst:
        print 'private_decrypt -> public_encrypt: not ok'

def test0():
    print 'testing misc.'
    print `pub.e`, `pub.n`
    print `priv.e`, `priv.n`

if __name__=='__main__':
    Rand.load_file('randpool.dat', -1) 
    test_encrypt('pkcs1_padding')
    test_encrypt('pkcs1_oaep_padding')
    #test_encrypt('sslv23_padding')
    test_sign('pkcs1_padding')
    Rand.save_file('randpool.dat')

