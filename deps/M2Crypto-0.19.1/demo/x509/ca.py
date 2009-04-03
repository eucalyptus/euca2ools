#!/usr/bin/env python

"""
How to create a CA certificate with Python.

WARNING: This sample only demonstrates how to use the objects and methods,
         not how to create a safe and correct certificate.

Copyright (c) 2004 Open Source Applications Foundation.
Author: Heikki Toivonen
"""

from M2Crypto import RSA, X509, EVP, m2, Rand, Err

# XXX Do I actually need more keys?
# XXX Check return values from functions

def generateRSAKey():
    return RSA.gen_key(2048, m2.RSA_F4)

def makePKey(key):
    pkey = EVP.PKey()
    pkey.assign_rsa(key)
    return pkey
    
def makeRequest(pkey):
    req = X509.Request()
    req.set_version(2)
    req.set_pubkey(pkey)
    name = X509.X509_Name()
    name.CN = 'My CA, Inc.'
    req.set_subject_name(name)
    ext1 = X509.new_extension('subjectAltName', 'DNS:foobar.example.com')
    ext2 = X509.new_extension('nsComment', 'Hello there')
    extstack = X509.X509_Extension_Stack()
    extstack.push(ext1)
    extstack.push(ext2)

    assert(extstack[1].get_name() == 'nsComment')
    
    req.add_extensions(extstack)
    req.sign(pkey, 'sha1')
    return req

def makeCert(req, caPkey):
    pkey = req.get_pubkey()
    #woop = makePKey(generateRSAKey())
    #if not req.verify(woop.pkey):
    if not req.verify(pkey):
        # XXX What error object should I use?
        raise ValueError, 'Error verifying request'
    sub = req.get_subject()
    # If this were a real certificate request, you would display
    # all the relevant data from the request and ask a human operator
    # if you were sure. Now we just create the certificate blindly based
    # on the request.
    cert = X509.X509()
    # We know we are making CA cert now...
    # Serial defaults to 0.
    cert.set_serial_number(1)
    cert.set_version(2)
    cert.set_subject(sub)
    issuer = X509.X509_Name()
    issuer.CN = 'The Issuer Monkey'
    issuer.O = 'The Organization Otherwise Known as My CA, Inc.'
    cert.set_issuer(issuer)
    cert.set_pubkey(pkey)
    notBefore = m2.x509_get_not_before(cert.x509)
    notAfter  = m2.x509_get_not_after(cert.x509)
    m2.x509_gmtime_adj(notBefore, 0)
    days = 30
    m2.x509_gmtime_adj(notAfter, 60*60*24*days)
    cert.add_ext(
        X509.new_extension('subjectAltName', 'DNS:foobar.example.com'))
    ext = X509.new_extension('nsComment', 'M2Crypto generated certificate')
    ext.set_critical(0)# Defaults to non-critical, but we can also set it
    cert.add_ext(ext)
    cert.sign(caPkey, 'sha1')

    assert(cert.get_ext('subjectAltName').get_name() == 'subjectAltName')
    assert(cert.get_ext_at(0).get_name() == 'subjectAltName')
    assert(cert.get_ext_at(0).get_value() == 'DNS:foobar.example.com')
    
    return cert

def ca():
    key = generateRSAKey()
    pkey = makePKey(key)
    req = makeRequest(pkey)
    cert = makeCert(req, pkey)
    return (cert, pkey)

if __name__ == '__main__':
    Rand.load_file('../randpool.dat', -1)
    rsa = generateRSAKey()
    pkey = makePKey(rsa)
    req = makeRequest(pkey)
    print req.as_text()
    cert = makeCert(req, pkey)
    print cert.as_text()
    print cert.as_pem()
    cert.save_pem('my_ca_cert.pem')
    rsa.save_key('my_key.pem', 'aes_256_cbc')
    Rand.save_file('../randpool.dat')
