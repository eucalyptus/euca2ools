"""Support for SSL socket timeouts.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

import struct
from M2Crypto import m2

DEFAULT_TIMEOUT = 600 

class timeout:

    def __init__(self, sec=DEFAULT_TIMEOUT, microsec=0):
        self.sec = sec
        self.microsec = microsec

    def pack(self):
        return struct.pack('ll', self.sec, self.microsec)


def struct_to_timeout(binstr):
    (s, ms) = struct.unpack('ll', binstr)
    return timeout(s, ms)

def struct_size():
    return struct.calcsize('ll')
