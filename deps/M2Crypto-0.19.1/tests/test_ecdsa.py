#!/usr/bin/env python

"""Unit tests for M2Crypto.EC, ECDSA part.

Copyright (c) 2000 Ng Pheng Siong. All rights reserved.
Portions copyright (c) 2005-2006 Vrije Universiteit Amsterdam. All rights reserved.
"""

import unittest
import sha
from M2Crypto import EC, BIO, Rand, m2

class ECDSATestCase(unittest.TestCase):

    errkey = 'tests/rsa.priv.pem'
    privkey = 'tests/ec.priv.pem'
    pubkey = 'tests/ec.pub.pem'

    data = sha.sha('Can you spell subliminal channel?').digest()

    def callback(self, *args):
        pass

    def callback2(self):
        pass

    def test_loadkey_junk(self):
        self.assertRaises(ValueError, EC.load_key, self.errkey)

    def test_loadkey(self):
        ec = EC.load_key(self.privkey)
        assert len(ec) == 233

    def test_loadpubkey(self):
        # XXX more work needed
        ec = EC.load_pub_key(self.pubkey)
        assert len(ec) == 233
        self.assertRaises(EC.ECError, EC.load_pub_key, self.errkey)

    def _test_sign_dsa(self):
        ec = EC.gen_params(EC.NID_sect233k1)
        # ec.gen_key()
        self.assertRaises(EC.ECError, ec.sign_dsa, self.data)
        ec = EC.load_key(self.privkey)
        r, s = ec.sign_dsa(self.data)
        assert ec.verify_dsa(self.data, r, s)
        assert not ec.verify_dsa(self.data, s, r)

    def test_sign_dsa_asn1(self):
        ec = EC.load_key(self.privkey)
        blob = ec.sign_dsa_asn1(self.data)
        assert ec.verify_dsa_asn1(self.data, blob)
        self.assertRaises(EC.ECError, ec.verify_dsa_asn1, blob, self.data)

    def test_verify_dsa(self):
        ec = EC.load_key(self.privkey)
        r, s = ec.sign_dsa(self.data)
        ec2 = EC.load_pub_key(self.pubkey)
        assert ec2.verify_dsa(self.data, r, s)
        assert not ec2.verify_dsa(self.data, s, r)
        
    def test_genparam(self):
        ec = EC.gen_params(EC.NID_sect233k1)
        assert len(ec) == 233


def suite():
    return unittest.makeSuite(ECDSATestCase)
    

if __name__ == '__main__':
    Rand.load_file('randpool.dat', -1) 
    unittest.TextTestRunner().run(suite())
    Rand.save_file('randpool.dat')

