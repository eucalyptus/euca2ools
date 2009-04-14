#!/usr/bin/env python

"""Unit tests for M2Crypto.BIO.IOBuffer.

Copyright (c) 2000 Ng Pheng Siong. All rights reserved."""

from cStringIO import StringIO

import unittest
import M2Crypto
from M2Crypto.BIO import IOBuffer, MemoryBuffer

class IOBufferTestCase(unittest.TestCase):

    def setUp(self):
        self._data = 'abcdef\n'
        self.data = self._data * 1024

    def tearDown(self):
        pass

    def test_init_empty(self):
        mb = MemoryBuffer()
        io = IOBuffer(mb)
        out = io.read()
        assert out == ''

    def test_init_something(self):
        mb = MemoryBuffer(self.data)
        io = IOBuffer(mb)
        out = io.read(len(self.data))
        assert out == self.data

    def test_read_less_than(self):
        chunk = len(self.data) - 7
        mb = MemoryBuffer(self.data)
        io = IOBuffer(mb)
        out = io.read(chunk)
        assert out == self.data[:chunk]
        
    def test_read_more_than(self):
        chunk = len(self.data) + 8
        mb = MemoryBuffer(self.data)
        io = IOBuffer(mb)
        out = io.read(chunk)
        assert out == self.data

    def test_readline(self):
        buf = StringIO()
        mb = MemoryBuffer(self.data)
        io = IOBuffer(mb)
        while 1:
            out = io.readline()
            if not out:
                break
            buf.write(out)
            assert out == self._data
        assert buf.getvalue() == self.data

    def test_readlines(self):
        buf = StringIO()
        mb = MemoryBuffer(self.data)
        io = IOBuffer(mb)
        lines = io.readlines()
        for line in lines:
            assert line == self._data
            buf.write(line)
        assert buf.getvalue() == self.data

    def test_closed(self):
        mb = MemoryBuffer(self.data)
        io = IOBuffer(mb)
        io.close()
        self.assertRaises(IOError, io.write, self.data)
        assert not io.readable() and not io.writeable()

    def test_read_only(self):
        mb = MemoryBuffer(self.data)
        io = IOBuffer(mb, mode='r')
        self.assertRaises(IOError, io.write, self.data)
        assert not io.writeable()


def suite():
    return unittest.makeSuite(IOBufferTestCase)
    

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())

