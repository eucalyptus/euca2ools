#!/usr/bin/env python

"""Unit tests for M2Crypto.BIO.MemoryBuffer.

Copyright (c) 2000 Ng Pheng Siong. All rights reserved."""

import unittest
import M2Crypto
from M2Crypto.BIO import MemoryBuffer

class MemoryBufferTestCase(unittest.TestCase):

    def setUp(self):
        self.data = 'abcdef' * 64

    def tearDown(self):
        pass

    def test_init_empty(self):
        mb = MemoryBuffer()
        assert len(mb) == 0
        out = mb.read()
        assert out is None

    def test_init_something(self):
        mb = MemoryBuffer(self.data)
        assert len(mb) == len(self.data)
        out = mb.read()
        assert out == self.data

    def test_read_less_than(self):
        chunk = len(self.data) - 7
        mb = MemoryBuffer(self.data)
        out = mb.read(chunk)
        assert out == self.data[:chunk] and len(mb) == (len(self.data) - chunk)
        
    def test_read_more_than(self):
        chunk = len(self.data) + 8
        mb = MemoryBuffer(self.data)
        out = mb.read(chunk)
        assert out == self.data and len(mb) == 0

    def test_write_close(self):
        mb = MemoryBuffer(self.data)
        assert mb.writeable()
        mb.write_close()
        assert mb.readable()
        self.assertRaises(IOError, mb.write, self.data)
        assert not mb.writeable()

    def test_closed(self):
        mb = MemoryBuffer(self.data)
        mb.close()
        self.assertRaises(IOError, mb.write, self.data)
        assert mb.readable() and not mb.writeable()


def suite():
    return unittest.makeSuite(MemoryBufferTestCase)
    

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())

