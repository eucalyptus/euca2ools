#!/usr/bin/env python

"""ECDH demonstration.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved.

Portions copyright (c) 2005-2006 Vrije Universiteit Amsterdam. 
All rights reserved."""

from M2Crypto import EC,Rand

def test():
    print 'generating ec keys:'
    a=EC.gen_params(EC.NID_sect233k1)
    a.gen_key()
    b=EC.gen_params(EC.NID_sect233k1)
    b.gen_key()
    a_shared_key = a.compute_dh_key(b.pub())
    b_shared_key = b.compute_dh_key(a.pub())
    print 'shared key according to a = ', `a_shared_key`
    print 'shared key according to b = ', `b_shared_key`
    if a_shared_key == b_shared_key:
        print 'ok'
    else:
        print 'not ok'


if __name__=='__main__':
    Rand.load_file('randpool.dat', -1) 
    test()
    Rand.save_file('randpool.dat')
