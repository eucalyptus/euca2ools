#!/usr/bin/env python

"""S/MIME demo.

Copyright (c) 2000 Ng Pheng Siong. All rights reserved."""

from M2Crypto import BIO, Rand, SMIME, X509
import sys

def decrypt_verify(p7file, recip_key, signer_cert, ca_cert):
    s = SMIME.SMIME()

    # Load decryption private key.
    s.load_key(recip_key)

    # Extract PKCS#7 blob from input.
    p7, bio = SMIME.smime_load_pkcs7_bio(p7file)

    # Decrypt.
    data = s.decrypt(p7)

    # Because we passed in a SignAndEnveloped blob, the output
    # of our decryption is a Signed blob. We now verify it.

    # Load the signer's cert.
    sk = X509.X509_Stack()
    s.set_x509_stack(sk)

    # Load the CA cert.
    st = X509.X509_Store()
    st.load_info(ca_cert)
    s.set_x509_store(st)

    # Verify.
    p7, bio = SMIME.smime_load_pkcs7_bio(BIO.MemoryBuffer(data))
    if bio is not None:
        # Netscape Messenger clear-signs, when also encrypting.
        data = s.verify(p7, bio)
    else:
        # M2Crypto's sendsmime.py opaque-signs, when also encrypting.
        data = s.verify(p7)

    print data


if __name__ == '__main__':
    Rand.load_file('../randpool.dat', -1) 
    decrypt_verify(BIO.File(sys.stdin), 'client.pem', 'client2.pem','ca.pem')
    Rand.save_file('../randpool.dat')

