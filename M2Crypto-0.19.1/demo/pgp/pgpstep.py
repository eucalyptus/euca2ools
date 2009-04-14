#!/usr/bin/env python

"""pgpstep - steps through a pgp2 packet stream.

Copyright (c) 1999 Ng Pheng Siong. All rights reserved."""

from M2Crypto import PGP, util
import time

def desc_public_key(pkt):
    print 'packet = public_key'
    print 'version =', pkt.version()
    print 'created = ', time.asctime(time.gmtime(pkt.timestamp()))
    print 'validity code =', pkt.validity()
    print 'pkc type =', `pkt.pkc()`
    #e, n = pkt.pubkey()
    print 'e =', `pkt._e`
    print 'n =', `pkt._n`
    print
    
def desc_trust(pkt):
    print 'packet = trust'
    print 'trustworthiness = <ignored>'
    print

def desc_userid(pkt):
    print 'packet = user_id'
    print 'user_id =', pkt.userid()
    print

def desc_signature(pkt):
    print 'packet = signature'
    print 'version =', pkt.version()
    print 'classification =', `pkt._classification`
    print 'created = ', time.asctime(time.gmtime(pkt.timestamp()))
    print 'keyid =', `pkt._keyid`
    print 'pkc type =', `pkt.pkc()`
    print 'md_algo =', `pkt._md_algo`
    print 'md_chksum =', `pkt._md_chksum`
    print 'sig =', `pkt._sig`
    print

def desc_private_key(pkt):
    print 'packet = private key'
    print 'version =', pkt.version()
    print 'created = ', time.asctime(time.gmtime(pkt.timestamp()))
    print 'validity code =', pkt.validity()
    print 'pkc type =', `pkt.pkc()`
    print 'e =', `pkt._e`
    print 'n =', `pkt._n`
    print 'cipher =', `pkt._cipher`
    if pkt._cipher == '\001':
        print 'following attributes are encrypted'
        print 'iv =', `pkt._iv`
    print 'd =', `pkt._d`
    print 'p =', `pkt._p`
    print 'q =', `pkt._q`
    print 'u =', `pkt._u`
    print 'checksum =', `pkt._cksum`
    print

def desc_cke(pkt):
    print 'packet = cke'
    print 'iv =', `pkt.iv`
    print 'checksum =', `pkt.cksum`
    print 'ciphertext =', `pkt.ctxt`
    print

def desc_pke(pkt):
    print 'packet = pke'
    print 'version =', pkt.version
    print 'keyid =', `pkt.keyid`
    print 'pkc type =', pkt.pkc_type
    print 'dek =', hex(pkt.dek)[:-1]
    print

def desc_literal(pkt):
    print 'packet = literal data'
    print 'mode =', `pkt.fmode`
    print 'filename =', pkt.fname
    print 'time = ', time.asctime(time.gmtime(pkt.ftime))
    print 'data = <%d octets of literal data>' % (len(pkt.data),)
    print

DESC = {
    PGP.public_key_packet: desc_public_key,
    PGP.trust_packet: desc_trust,
    PGP.userid_packet: desc_userid,
    PGP.signature_packet: desc_signature,
    PGP.private_key_packet: desc_private_key,
    PGP.cke_packet: desc_cke,
    PGP.pke_packet: desc_pke,
    PGP.literal_packet: desc_literal,
}

if __name__ == '__main__':
    import sys
    count = 0
    for arg in sys.argv[1:]:
	    f = open(arg, 'rb')
	    ps = PGP.packet_stream(f)
	    while 1:
	        pkt = ps.read()
	        if pkt is None:
	            break
	        elif pkt:
	            print '-'*70
	            DESC[pkt.__class__](pkt)
	    count = count + ps.count()
	    ps.close()
    print '-'*70
    print 'Total octets processed =', count

