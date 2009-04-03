#!/usr/bin/env python2.0

"""Demonstrates the use of m2.bio_set_mem_eof_return().
Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from M2Crypto import m2
m2.lib_init()

use_mem = 1

if use_mem:
    bio = m2.bio_new(m2.bio_s_mem())
else:
    bio = m2.bio_new_file('XXX', 'wb')
ciph = m2.bf_cbc()
filt = m2.bio_new(m2.bio_f_cipher())
m2.bio_set_cipher(filt, ciph, 'key', 'iv', 1)
m2.bio_push(filt, bio)
m2.bio_write(filt, '12345678901234567890')
m2.bio_flush(filt)
m2.bio_pop(filt)
m2.bio_free(filt)
if use_mem:
    m2.bio_set_mem_eof_return(bio, 0)
    xxx = m2.bio_read(bio, 100)
    print `xxx`, len(xxx)
m2.bio_free(bio)

if use_mem:
    bio = m2.bio_new(m2.bio_s_mem())
    m2.bio_write(bio, xxx)
    m2.bio_set_mem_eof_return(bio, 0)
else:
    bio = m2.bio_new_file('XXX', 'rb')
ciph = m2.bf_cbc()
filt = m2.bio_new(m2.bio_f_cipher())
m2.bio_set_cipher(filt, ciph, 'key', 'iv', 0)
m2.bio_push(filt, bio)
yyy = m2.bio_read(filt, 100)
print `yyy`
m2.bio_pop(filt)
m2.bio_free(filt)
m2.bio_free(bio)

