#!/usr/bin/env python

"""Unit tests for M2Crypto.SMIME.

Copyright (C) 2006 Open Source Applications Foundation. All Rights Reserved.
"""

import unittest
from M2Crypto import SMIME, BIO, Rand, X509

class SMIMETestCase(unittest.TestCase):
    cleartext = 'some text to manipulate'

    def setUp(self):
        # XXX Ugly, but not sure what would be better
        self.signed = self.test_sign()
        self.encrypted = self.test_encrypt()
    
    def test_sign(self):
        buf = BIO.MemoryBuffer(self.cleartext)
        s = SMIME.SMIME()
        s.load_key('tests/signer_key.pem', 'tests/signer.pem')
        p7 = s.sign(buf)
        assert len(buf) == 0
        assert p7.type() == SMIME.PKCS7_SIGNED, p7.type()
        assert isinstance(p7, SMIME.PKCS7), p7
        out = BIO.MemoryBuffer()
        p7.write(out)
        
        buf = out.read()
        
        assert buf[:len('-----BEGIN PKCS7-----')] == '-----BEGIN PKCS7-----'
        buf = buf.strip()
        assert buf[-len('-----END PKCS7-----'):] == '-----END PKCS7-----', buf[-len('-----END PKCS7-----'):]
        assert len(buf) > len('-----END PKCS7-----') + len('-----BEGIN PKCS7-----')
        
        s.write(out, p7, BIO.MemoryBuffer(self.cleartext))
        return out

    def test_store_load_info(self):        
        st = X509.X509_Store()
        self.assertRaises(X509.X509Error, st.load_info, 'tests/ca.pem-typoname')
        self.assertEqual(st.load_info('tests/ca.pem'), 1) 

    def test_verify(self):
        s = SMIME.SMIME()
        
        x509 = X509.load_cert('tests/signer.pem')
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)
        
        st = X509.X509_Store()
        st.load_info('tests/ca.pem')
        s.set_x509_store(st)
        
        p7, data = SMIME.smime_load_pkcs7_bio(self.signed)
        
        assert data.read() == self.cleartext
        assert isinstance(p7, SMIME.PKCS7), p7
        v = s.verify(p7)
        assert v == self.cleartext
    
        t = p7.get0_signers(sk)
        assert len(t) == 1
        assert t[0].as_pem() == x509.as_pem(), t[0].as_text()

    def test_verifyBad(self):
        s = SMIME.SMIME()
        
        x509 = X509.load_cert('tests/recipient.pem')
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)
        
        st = X509.X509_Store()
        st.load_info('tests/recipient.pem')
        s.set_x509_store(st)
        
        p7, data = SMIME.smime_load_pkcs7_bio(self.signed)
        assert data.read() == self.cleartext
        assert isinstance(p7, SMIME.PKCS7), p7
        self.assertRaises(SMIME.PKCS7_Error, s.verify, p7) # Bad signer

    def test_encrypt(self):
        buf = BIO.MemoryBuffer(self.cleartext)
        s = SMIME.SMIME()

        x509 = X509.load_cert('tests/recipient.pem')
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)

        s.set_cipher(SMIME.Cipher('des_ede3_cbc'))
        p7 = s.encrypt(buf)
        
        assert len(buf) == 0
        assert p7.type() == SMIME.PKCS7_ENVELOPED, p7.type()
        assert isinstance(p7, SMIME.PKCS7), p7
        out = BIO.MemoryBuffer()
        p7.write(out)
    
        buf = out.read()
        
        assert buf[:len('-----BEGIN PKCS7-----')] == '-----BEGIN PKCS7-----'
        buf = buf.strip()
        assert buf[-len('-----END PKCS7-----'):] == '-----END PKCS7-----'
        assert len(buf) > len('-----END PKCS7-----') + len('-----BEGIN PKCS7-----')
        
        s.write(out, p7)
        return out
    
    def test_decrypt(self):
        s = SMIME.SMIME()

        s.load_key('tests/recipient_key.pem', 'tests/recipient.pem')
        
        p7, data = SMIME.smime_load_pkcs7_bio(self.encrypted)
        assert isinstance(p7, SMIME.PKCS7), p7
        self.assertRaises(SMIME.SMIME_Error, s.verify, p7) # No signer
        
        out = s.decrypt(p7)
        assert out == self.cleartext

    def test_decryptBad(self):
        s = SMIME.SMIME()

        s.load_key('tests/signer_key.pem', 'tests/signer.pem')
        
        p7, data = SMIME.smime_load_pkcs7_bio(self.encrypted)
        assert isinstance(p7, SMIME.PKCS7), p7
        self.assertRaises(SMIME.SMIME_Error, s.verify, p7) # No signer

        # Cannot decrypt: no recipient matches certificate
        self.assertRaises(SMIME.PKCS7_Error, s.decrypt, p7)

    def test_signEncryptDecryptVerify(self):
        # sign
        buf = BIO.MemoryBuffer(self.cleartext)
        s = SMIME.SMIME()    
        s.load_key('tests/signer_key.pem', 'tests/signer.pem')
        p7 = s.sign(buf)
        
        # encrypt
        x509 = X509.load_cert('tests/recipient.pem')
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)
    
        s.set_cipher(SMIME.Cipher('des_ede3_cbc'))
        
        tmp = BIO.MemoryBuffer()
        s.write(tmp, p7, buf)

        p7 = s.encrypt(tmp)
        
        signedEncrypted = BIO.MemoryBuffer()
        s.write(signedEncrypted, p7)

        # decrypt
        s = SMIME.SMIME()
    
        s.load_key('tests/recipient_key.pem', 'tests/recipient.pem')
        
        p7, data = SMIME.smime_load_pkcs7_bio(signedEncrypted)
        
        out = s.decrypt(p7)
        
        # verify
        x509 = X509.load_cert('tests/signer.pem')
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)
        
        st = X509.X509_Store()
        st.load_info('tests/ca.pem')
        s.set_x509_store(st)
        
        p7_bio = BIO.MemoryBuffer(out)
        p7, data = SMIME.smime_load_pkcs7_bio(p7_bio)
        v = s.verify(p7)
        assert v == self.cleartext


class WriteLoadTestCase(unittest.TestCase):
    def setUp(self):
        s = SMIME.SMIME()
        s.load_key('tests/signer_key.pem', 'tests/signer.pem')
        p7 = s.sign(BIO.MemoryBuffer('some text'))
        self.filename = 'tests/sig.p7'
        f = BIO.openfile(self.filename, 'wb')
        assert p7.write(f) == 1
        f.close()

        self.filenameSmime = 'tests/sig.p7s'
        f = BIO.openfile(self.filenameSmime, 'wb')
        assert s.write(f, p7, BIO.MemoryBuffer('some text')) == 1
        f.close()
        
    def test_write_pkcs7_der(self):
        buf = BIO.MemoryBuffer()
        assert SMIME.load_pkcs7(self.filename).write_der(buf) == 1
        s = buf.read()
        assert len(s) == 1155, len(s)
        
    def test_load_pkcs7(self):
        assert SMIME.load_pkcs7(self.filename).type() == SMIME.PKCS7_SIGNED
    
    def test_load_pkcs7_bio(self):
        f = open(self.filename, 'rb')
        buf = BIO.MemoryBuffer(f.read())
        f.close()
        
        assert SMIME.load_pkcs7_bio(buf).type() == SMIME.PKCS7_SIGNED

    def test_load_smime(self):
        a, b = SMIME.smime_load_pkcs7(self.filenameSmime)
        assert isinstance(a, SMIME.PKCS7), a
        assert isinstance(b, BIO.BIO), b
        assert a.type() == SMIME.PKCS7_SIGNED
        
    def test_load_smime_bio(self):
        f = open(self.filenameSmime, 'rb')
        buf = BIO.MemoryBuffer(f.read())
        f.close()

        a, b = SMIME.smime_load_pkcs7_bio(buf)
        assert isinstance(a, SMIME.PKCS7), a
        assert isinstance(b, BIO.BIO), b
        assert a.type() == SMIME.PKCS7_SIGNED


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SMIMETestCase))
    suite.addTest(unittest.makeSuite(WriteLoadTestCase))
    return suite


if __name__ == '__main__':
    Rand.load_file('randpool.dat', -1)
    unittest.TextTestRunner().run(suite())
    Rand.save_file('randpool.dat')

