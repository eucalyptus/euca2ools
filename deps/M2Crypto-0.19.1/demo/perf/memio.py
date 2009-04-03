#!/usr/bin/env python2.0

"""A comparison of Python's cStringIO and M2Crypto's MemoryBuffer,
the outcome of which is that MemoryBuffer suffers from doing too much
in Python. 

Two way to optimise MemoryBuffer:
1. Create MemoryBufferIn and MemoryBufferOut a la StringI and StringO.
2. Have MemoryBuffer do all internal work with cStringIO. ;-)
"""

from cStringIO import StringIO
from M2Crypto.BIO import MemoryBuffer
from M2Crypto import m2
import profile

txt = 'Python, Smalltalk, Haskell, Scheme, Lisp, Self, Erlang, ML, ...'

def stringi(iter, txt=txt):
    buf = StringIO()
    for i in range(iter):
        buf.write(txt)
    out = buf.getvalue()

def membufi(iter, txt=txt):
    buf = MemoryBuffer()
    for i in range(iter):
        buf.write(txt)
    out = buf.getvalue()

def membuf2i(iter, txt=txt):
    buf = MemoryBuffer()
    buf.write(txt * iter)
    out = buf.getvalue()

def cmembufi(iter, txt=txt):
    buf = m2.bio_new(m2.bio_s_mem())
    for i in range(iter):
        m2.bio_write(buf, txt)
    m2.bio_set_mem_eof_return(buf, 0)
    out = m2.bio_read(buf, m2.bio_ctrl_pending(buf))

if __name__ == '__main__':
    profile.run('stringi(10000)')
    profile.run('cmembufi(10000)')
    profile.run('membufi(10000)')
    profile.run('membuf2i(10000)')


