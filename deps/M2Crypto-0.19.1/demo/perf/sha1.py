#!/usr/bin/env python2.0

"""A comparison of Python's sha and M2Crypto.EVP.MessageDigest, 
the outcome of which is that EVP.MessageDigest suffers from doing 
too much in Python."""

import profile

from sha import sha
import M2Crypto
from M2Crypto import m2
from M2Crypto.EVP import MessageDigest

txt = 'Python, Smalltalk, Haskell, Scheme, Lisp, Self, Erlang, ML, ...'

def py_sha(iter, txt=txt):
    s = sha()
    for i in range(iter):
        s.update(txt)
    out = s.digest()

def m2_sha(iter, txt=txt):
    s = MessageDigest('sha1')
    for i in range(iter):
        s.update(txt)
    out = s.digest()

def m2_sha_2(iter, txt=txt):
    s = MessageDigest('sha1')
    s.update(txt * iter)
    out = s.digest()

def m2c_sha(iter, txt=txt):
    ctx = m2.md_ctx_new()
    m2.digest_init(ctx, m2.sha1())
    for i in range(iter):
        m2.digest_update(ctx, txt)
    out = m2.digest_final(ctx)

if __name__ == '__main__':
    profile.run('py_sha(10000)')
    profile.run('m2_sha(10000)')
    profile.run('m2_sha_2(10000)')
    profile.run('m2c_sha(10000)')


