#!/usr/bin/env python

"""S/MIME demo.

Copyright (c) 2000 Ng Pheng Siong. All rights reserved."""

from M2Crypto import BIO, Rand, SMIME, X509

ptxt = """
S/MIME - Secure Multipurpose Internet Mail Extensions [RFC 2311, RFC 2312] - 
provides a consistent way to send and receive secure MIME data. Based on the
popular Internet MIME standard, S/MIME provides the following cryptographic
security services for electronic messaging applications - authentication,
message integrity and non-repudiation of origin (using digital signatures)
and privacy and data security (using encryption).

S/MIME is built on the PKCS #7 standard. [PKCS7]

S/MIME is implemented in Netscape Messenger and Microsoft Outlook.
"""

def makebuf():
    buf = BIO.MemoryBuffer(ptxt)
    return buf

def sign():
    print 'test sign & save...',
    buf = makebuf()
    s = SMIME.SMIME()
    s.load_key('client.pem')
    p7 = s.sign(buf)
    out = BIO.openfile('clear.p7', 'w')
    out.write('To: ngps@post1.com\n')
    out.write('From: ngps@post1.com\n')
    out.write('Subject: testing\n')
    buf = makebuf() # Recreate buf, because sign() has consumed it.
    s.write(out, p7, buf)
    out.close()

    buf = makebuf()
    p7 = s.sign(buf)
    out = BIO.openfile('opaque.p7', 'w')
    out.write('To: ngps@post1.com\n')
    out.write('From: ngps@mpost1.com\n')
    out.write('Subject: testing\n')
    s.write(out, p7)
    out.close()
    print 'ok'

def verify_clear():
    print 'test load & verify clear...',
    s = SMIME.SMIME()
    x509 = X509.load_cert('client.pem')
    sk = X509.X509_Stack()
    sk.push(x509)
    s.set_x509_stack(sk)
    st = X509.X509_Store()
    st.load_info('ca.pem')
    s.set_x509_store(st)
    p7, data = SMIME.smime_load_pkcs7('clear.p7')
    v = s.verify(p7)
    if v:
        print 'ok'
    else:
        print 'not ok'
    
def verify_opaque():
    print 'test load & verify opaque...',
    s = SMIME.SMIME()
    x509 = X509.load_cert('client.pem')
    sk = X509.X509_Stack()
    sk.push(x509)
    s.set_x509_stack(sk)
    st = X509.X509_Store()
    st.load_info('ca.pem')
    s.set_x509_store(st)
    p7, data = SMIME.smime_load_pkcs7('opaque.p7')
    v = s.verify(p7, data)
    if v:
        print 'ok'
    else:
        print 'not ok'
    
def verify_netscape():
    print 'test load & verify netscape messager output...',
    s = SMIME.SMIME()
    #x509 = X509.load_cert('client.pem')
    sk = X509.X509_Stack()
    #sk.push(x509)
    s.set_x509_stack(sk)
    st = X509.X509_Store()
    st.load_info('ca.pem')
    s.set_x509_store(st)
    p7, data = SMIME.smime_load_pkcs7('ns.p7')
    v = s.verify(p7, data)
    print '\n', v, '\n...ok'

    
def sv():
    print 'test sign/verify...',
    buf = makebuf()
    s = SMIME.SMIME()

    # Load a private key.
    s.load_key('client.pem')

    # Sign.
    p7 = s.sign(buf)

    # Output the stuff.
    bio = BIO.MemoryBuffer()
    s.write(bio, p7, buf)
    
    # Plumbing for verification: CA's cert.
    st = X509.X509_Store()
    st.load_info('ca.pem')
    s.set_x509_store(st)

    # Plumbing for verification: Signer's cert.
    x509 = X509.load_cert('client.pem')
    sk = X509.X509_Stack()
    sk.push(x509)
    s.set_x509_stack(sk)

    # Verify.
    p7, buf = SMIME.smime_load_pkcs7_bio(bio)
    v = s.verify(p7, flags=SMIME.PKCS7_DETACHED)
    
    if v:
        print 'ok'
    else:
        print 'not ok'

def ed():
    print 'test encrypt/decrypt...',
    buf = makebuf()
    s = SMIME.SMIME()

    # Load target cert to encrypt to.
    x509 = X509.load_cert('client.pem')
    sk = X509.X509_Stack()
    sk.push(x509)
    s.set_x509_stack(sk)

    # Add a cipher.
    s.set_cipher(SMIME.Cipher('bf_cbc')) 

    # Encrypt.
    p7 = s.encrypt(buf)
    
    # Load target's private key.
    s.load_key('client.pem')

    # Decrypt.
    data = s.decrypt(p7)
    
    if data:
        print 'ok'
    else:
        print 'not ok'


def zope_test():
    print 'test zophistry...'
    f = open('client.pem')
    cert_str = f.read()
    key_bio = BIO.MemoryBuffer(cert_str)    
    cert_bio = BIO.MemoryBuffer(cert_str)   # XXX Kludge.
    s = SMIME.SMIME()
    s.load_key_bio(key_bio, cert_bio)
    # XXX unfinished...


def leak_test():
    # Seems ok, not leaking.
    while 1:
        ed()
        #sv()


if __name__ == '__main__':
    Rand.load_file('../randpool.dat', -1) 
    ed()
    sign()
    verify_opaque()
    verify_clear()
    #verify_netscape()
    sv()
    #zope_test()
    #leak_test()
    Rand.save_file('../randpool.dat')

