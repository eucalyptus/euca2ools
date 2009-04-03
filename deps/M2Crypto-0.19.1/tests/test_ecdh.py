#!/usr/bin/env python

"""Unit tests for M2Crypto.EC, ECDH part.

Copyright (c) 2000 Ng Pheng Siong. All rights reserved.
Portions copyright (c) 2005-2006 Vrije Universiteit Amsterdam. All rights reserved.
"""


import unittest
from M2Crypto import EC, BIO, Rand, m2
import sys

class ECDHTestCase(unittest.TestCase):

    privkey = 'tests/ec.priv.pem'

    def test_init_junk(self):
        self.assertRaises(TypeError, EC.EC, 'junk')

    def test_compute_key(self):
        a = EC.load_key(self.privkey)
        b = EC.gen_params(EC.NID_sect233k1)
        b.gen_key()
        ak = a.compute_dh_key(b.pub())
        bk = b.compute_dh_key(a.pub())
        assert ak == bk

    def test_pubkey_from_der(self):
        a = EC.gen_params(EC.NID_sect233k1)
        a.gen_key()
        b = EC.gen_params(EC.NID_sect233k1)
        b.gen_key()
        a_pub_der = a.pub().get_der()
        a_pub = EC.pub_key_from_der(a_pub_der)
        ak = a.compute_dh_key(b.pub())
        bk = b.compute_dh_key(a_pub)
        assert ak == bk


def suite():
    return unittest.makeSuite(ECDHTestCase)


if __name__=='__main__':
    Rand.load_file('randpool.dat', -1) 
    unittest.TextTestRunner().run(suite())
    Rand.save_file('randpool.dat')

