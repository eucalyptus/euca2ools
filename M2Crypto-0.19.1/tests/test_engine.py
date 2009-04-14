#!/usr/bin/env python

"""Unit tests for M2Crypto.Engine."""

import unittest
from M2Crypto import Engine, m2

class EngineTestCase(unittest.TestCase):

    privkey = 'tests/rsa.priv.pem'
    bad_id = '1bea1edfeb97'

    def tearDown(self):
        Engine.cleanup()

    def test_by_id_junk(self):
        self.assertRaises(ValueError, Engine.Engine, self.bad_id)

    def test_by_id_openssl(self):
        Engine.load_openssl()
        Engine.Engine('openssl')
        
    def test_by_id_dynamic(self):
        Engine.load_dynamic()
        Engine.Engine('dynamic')
        
    def test_load_private(self):
        Engine.load_openssl()
        e = Engine.Engine('openssl')
        e.set_default()
        e.load_private_key(self.privkey)

    def test_load_certificate(self):
        Engine.load_openssl()
        e = Engine.Engine('openssl')
        e.set_default()
        self.assertRaises(Engine.EngineError, e.load_certificate, '/dev/null')

def suite():
    return unittest.makeSuite(EngineTestCase)
    

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())

