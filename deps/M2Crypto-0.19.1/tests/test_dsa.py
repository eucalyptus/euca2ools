#!/usr/bin/env python

"""Unit tests for M2Crypto.DSA.

Copyright (c) 2000 Ng Pheng Siong. All rights reserved."""

import unittest
import sha
from M2Crypto import DSA, BIO, Rand, m2

class DSATestCase(unittest.TestCase):

    errkey  = 'tests/rsa.priv.pem'
    privkey = 'tests/dsa.priv.pem'
    pubkey  = 'tests/dsa.pub.pem'
    param   = 'tests/dsa.param.pem'

    data = sha.sha('Can you spell subliminal channel?').digest()
    different_data = sha.sha('I can spell.').digest()

    def callback(self, *args):
        pass

    def test_loadkey_junk(self):
        self.assertRaises(DSA.DSAError, DSA.load_key, self.errkey)

    def test_loadkey(self):
        dsa = DSA.load_key(self.privkey)
        assert len(dsa) == 512

    def test_loadparam(self):
        self.assertRaises(DSA.DSAError, DSA.load_key, self.param)
        dsa = DSA.load_params(self.param)
        assert not dsa.check_key()
        assert len(dsa) == 512

    def test_sign(self):
        dsa = DSA.load_key(self.privkey)
        assert dsa.check_key()
        r, s = dsa.sign(self.data)
        assert dsa.verify(self.data, r, s)
        assert not dsa.verify(self.data, s, r)

    def test_sign_asn1(self):
        dsa = DSA.load_key(self.privkey)
        blob = dsa.sign_asn1(self.data)
        assert dsa.verify_asn1(self.data, blob)

    def test_sign_with_params_only(self):
        dsa = DSA.load_params(self.param)
        self.assertRaises(AssertionError, dsa.sign, self.data)
        self.assertRaises(AssertionError, dsa.sign_asn1, self.data)

    def test_pub_verify(self):
        dsa = DSA.load_key(self.privkey)
        r, s = dsa.sign(self.data)
        dsapub = DSA.load_pub_key(self.pubkey)
        assert dsapub.check_key()
        assert dsapub.verify(self.data, r, s)

    def test_verify_fail(self):
        dsa = DSA.load_key(self.privkey)
        r, s = dsa.sign(self.data)
        assert not dsa.verify(self.different_data, r, s)

    def test_verify_fail2(self):
        dsa = DSA.load_key(self.privkey)
        r,s = dsa.sign(self.data)
        dsa2 = DSA.load_params(self.param)
        assert not dsa2.check_key()
        self.assertRaises(AssertionError, dsa2.verify, self.data, r, s)

    def test_genparam_setparam_genkey(self):
        dsa = DSA.gen_params(256, self.callback)
        assert len(dsa) == 512
        p = dsa.p
        q = dsa.q
        g = dsa.g
        dsa2 = DSA.set_params(p,q,g)
        assert not dsa2.check_key()
        dsa2.gen_key()
        assert dsa2.check_key()
        r,s = dsa2.sign(self.data)
        assert dsa2.verify(self.data, r, s)

def suite():
    return unittest.makeSuite(DSATestCase)
    

if __name__ == '__main__':
    Rand.load_file('randpool.dat', -1) 
    unittest.TextTestRunner().run(suite())
    Rand.save_file('randpool.dat')

