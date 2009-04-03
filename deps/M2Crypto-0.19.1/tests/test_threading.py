#!/usr/bin/env python

"""Unit tests for M2Crypto.threading.

Copyright (C) 2007 Open Source Applications Foundation. All Rights Reserved.
"""

import unittest
from M2Crypto import threading as m2threading, Rand


class ThreadingTestCase(unittest.TestCase):

    def setUp(self):
        m2threading.init()

    def tearDown(self):
        m2threading.cleanup()

    def test_pass(self):
        pass

    def test_multiInitCleanup(self):
        m2threading.init()
        m2threading.init()
        m2threading.cleanup()
        m2threading.cleanup()

        m2threading.init()
        m2threading.cleanup()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ThreadingTestCase))
    return suite


if __name__ == '__main__':
    Rand.load_file('randpool.dat', -1)
    unittest.TextTestRunner().run(suite())
    Rand.save_file('randpool.dat')
