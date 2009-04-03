#!/usr/bin/env python

"""Unit tests for M2Crypto.Rand.

Copyright (C) 2006 Open Source Applications Foundation (OSAF). All Rights Reserved.
"""

import unittest
import os, sys
from M2Crypto import Rand

class RandTestCase(unittest.TestCase):
    def test_bytes(self):
        self.assertRaises(MemoryError, Rand.rand_bytes, -1)
        assert Rand.rand_bytes(0) == ''
        assert len(Rand.rand_bytes(1)) == 1
        
    def test_pseudo_bytes(self):
        self.assertRaises(MemoryError, Rand.rand_pseudo_bytes, -1)
        assert Rand.rand_pseudo_bytes(0) == ('', 1)
        a, b = Rand.rand_pseudo_bytes(1)
        assert len(a) == 1
        assert b == 1
        
    def test_load_save(self):
        try:
            os.remove('tests/randpool.dat')
        except OSError:
            pass
        assert Rand.load_file('tests/randpool.dat', -1) == 0
        assert Rand.save_file('tests/randpool.dat') == 1024
        assert Rand.load_file('tests/randpool.dat', -1) == 1024
        
    def test_seed_add(self):
        if sys.version_info >= (2, 4):
            assert Rand.rand_seed(os.urandom(1024)) is None
            
            # XXX Should there be limits on the entropy parameter?
            assert Rand.rand_add(os.urandom(2), 0.5) is None
            Rand.rand_add(os.urandom(2), -0.5)
            Rand.rand_add(os.urandom(2), 5000.0)

        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RandTestCase))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
