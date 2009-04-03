#!/usr/bin/env python

"""HMAC demonstration.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from M2Crypto import EVP, Rand
from M2Crypto.util import h2b

data1=['', 'More text test vectors to stuff up EBCDIC machines :-)', \
    h2b("e9139d1e6ee064ef8cf514fc7dc83e86")]

data2=[h2b('0b'*16), "Hi There", \
    h2b("9294727a3638bb1c13f48ef8158bfc9d")]

data3=['Jefe', "what do ya want for nothing?", \
    h2b("750c783e6ab0b503eaa86e310a5db738")]

data4=[h2b('aa'*16), h2b('dd'*50), \
    h2b("56be34521d144c88dbb8c733f0e8b3f6")]

data=[data1, data2, data3, data4]

def test():
    print 'testing hmac'
    algo='md5'
    for d in data:
        h=EVP.HMAC(d[0], algo)
        h.update(d[1])
        ret=h.final()
        if ret!=d[2]:
            print data.index(d)+1, 'not ok' 
        else:
            print 'ok'

def make_chain_HMAC(key, start, input, algo='sha1'):
    chain = []
    hmac = EVP.HMAC(key, algo)
    hmac.update(`start`)
    digest = hmac.final()
    chain.append((digest, start))
    for i in input:
        hmac.reset(digest)
        hmac.update(`i`)
        digest = hmac.final()
        chain.append((digest, i))
    return chain

def make_chain_hmac(key, start, input, algo='sha1'):
    from M2Crypto.EVP import hmac
    chain = []
    digest = hmac(key, `start`, algo)
    chain.append((digest, start))
    for i in input:
        digest = hmac(digest, `i`, algo)
        chain.append((digest, i))
    return chain

def verify_chain_hmac(key, start, chain, algo='sha1'):
    from M2Crypto.EVP import hmac
    digest = hmac(key, `start`, algo)
    c = chain[0]
    if c[0] != digest or c[1] != start:
        print 'verify failed'
        return 0
    for d, v in chain[1:]:
        digest = hmac(digest, `v`, algo)
        if digest != d:
            print 'verify failed'
            return 0
    print 'ok'
    return 1

def verify_chain_HMAC(key, start, chain, algo='sha1'):
    hmac = EVP.HMAC(key, algo)
    hmac.update(`start`)
    digest = hmac.final()
    c = chain[0]
    if c[0] != digest or c[1] != start:
        print 'verify failed'
        return 0
    for d, v in chain[1:]:
        hmac.reset(digest)
        hmac.update(`v`)
        digest = hmac.final()
        if digest != d:
            print 'verify failed'
            return 0
    print 'ok'
    return 1

def test2():
    make_chain = make_chain_hmac
    verify_chain = verify_chain_hmac
    print 'testing hash-chaining'
    key = 'numero uno'
    start = 'zeroth item'
    input = ['first item', 'go go go', 'fly fly fly']
    chain = make_chain(key, start, input)
    print 'expect failure:',
    verify_chain('some key', start, chain)
    print 'expect success:',
    verify_chain(key, start, chain)

def t3():
    key = 'key'
    start = '0'
    input = xrange(10000) 
    make_chain_hmac(key, start, input)
    make_chain_HMAC(key, start, input)

def test3():
    import profile
    print 'testing hmac performance'
    profile.run('t3()')
    # Empirically, hmac() calls are faster than HMAC object calls.


if __name__=='__main__':
    Rand.load_file('randpool.dat', -1) 
    #test()
    test2()
    #test3()
    Rand.save_file('randpool.dat')

