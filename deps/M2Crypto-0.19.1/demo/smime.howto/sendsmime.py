#!/usr/bin/env python

"""S/MIME sender.

Copyright (c) 1999-2001 Ng Pheng Siong. All rights reserved."""

from M2Crypto import BIO, Rand, SMIME, X509
import smtplib, string, sys

def sendsmime(from_addr, to_addrs, subject, msg, from_key, from_cert=None, to_certs=None, smtpd='localhost'):

    msg_bio = BIO.MemoryBuffer(msg)
    sign = from_key
    encrypt = to_certs

    s = SMIME.SMIME()
    if sign:
        s.load_key(from_key, from_cert)
        p7 = s.sign(msg_bio, flags=SMIME.PKCS7_TEXT)
        msg_bio = BIO.MemoryBuffer(msg) # Recreate coz sign() has consumed it.

    if encrypt:
        sk = X509.X509_Stack()
        for x in to_certs:
            sk.push(X509.load_cert(x))
        s.set_x509_stack(sk)
        s.set_cipher(SMIME.Cipher('rc2_40_cbc')) 
        tmp_bio = BIO.MemoryBuffer()
        if sign:
            s.write(tmp_bio, p7)
        else:
            tmp_bio.write(msg)
        p7 = s.encrypt(tmp_bio)

    out = BIO.MemoryBuffer()
    out.write('From: %s\r\n' % from_addr)
    out.write('To: %s\r\n' % string.join(to_addrs, ", "))
    out.write('Subject: %s\r\n' % subject) 
    if encrypt:
        s.write(out, p7)
    else:
        if sign:
            s.write(out, p7, msg_bio, SMIME.PKCS7_TEXT)
        else:
            out.write('\r\n')
            out.write(msg)
    out.close()

    smtp = smtplib.SMTP()
    smtp.connect(smtpd)
    smtp.sendmail(from_addr, to_addrs, out.read())
    smtp.quit()

    # XXX Cleanup the stack and store.


msg = """
S/MIME - Secure Multipurpose Internet Mail Extensions [RFC 2311, RFC 2312] - 
provides a consistent way to send and receive secure MIME data. Based on the
popular Internet MIME standard, S/MIME provides the following cryptographic
security services for electronic messaging applications - authentication,
message integrity and non-repudiation of origin (using digital signatures)
and privacy and data security (using encryption).

S/MIME is built on the PKCS #7 standard. [PKCS7]

S/MIME is implemented in Netscape Messenger and Microsoft Outlook.
"""


if __name__ == '__main__':
    Rand.load_file('../randpool.dat', -1) 
    sendsmime(from_addr = 'ngps@post1.com', 
                to_addrs = ['popuser@nova.dyndns.org'],
                subject = 'S/MIME testing',
                msg = msg,
                #from_key = 'signer.pem',
                from_key = None,
                #to_certs = None)
                to_certs = ['recipient.pem'])
    Rand.save_file('../randpool.dat')

