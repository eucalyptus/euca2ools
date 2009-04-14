#!/usr/bin/env python

"""
Unit tests for M2Crypto.EVP.

Copyright (c) 2004-2007 Open Source Applications Foundation
Author: Heikki Toivonen
"""

import unittest
import cStringIO, sha
from binascii import hexlify, unhexlify
from M2Crypto import EVP, RSA, util, Rand, m2

class EVPTestCase(unittest.TestCase):
    def _gen_callback(self, *args):
        pass
    
    def _pass_callback(self, *args):
        return 'foobar'
    
    def _assign_rsa(self):
        rsa = RSA.gen_key(512, 3, callback=self._gen_callback)
        pkey = EVP.PKey()
        pkey.assign_rsa(rsa, capture=0) # capture=1 should cause crash
        return rsa
    
    def test_assign(self):
        rsa = self._assign_rsa()
        rsa.check_key()
        
    def test_pem(self):
        rsa = RSA.gen_key(512, 3, callback=self._gen_callback)
        pkey = EVP.PKey()
        pkey.assign_rsa(rsa)
        assert pkey.as_pem(callback=self._pass_callback) != pkey.as_pem(cipher=None)
        self.assertRaises(ValueError, pkey.as_pem, cipher='noXX$$%%suchcipher',
                          callback=self._pass_callback)
                          
    def test_as_der(self):
        """
        Test DER encoding the PKey instance after assigning 
        a RSA key to it.
        """
        rsa = RSA.gen_key(512, 3, callback=self._gen_callback)
        pkey = EVP.PKey()
        pkey.assign_rsa(rsa)
        der_blob = pkey.as_der()        
        #A quick but not thorough sanity check
        assert len(der_blob) == 92
          
        
    def test_MessageDigest(self):
        self.assertRaises(ValueError, EVP.MessageDigest, 'sha513')
        md = EVP.MessageDigest('sha1')
        assert md.update('Hello') == 1
        assert util.octx_to_num(md.final()) == 1415821221623963719413415453263690387336440359920

    def test_as_der_capture_key(self):
        """
        Test DER encoding the PKey instance after assigning 
        a RSA key to it. Have the PKey instance capture the RSA key.
        """
        rsa = RSA.gen_key(512, 3, callback=self._gen_callback)
        pkey = EVP.PKey()
        pkey.assign_rsa(rsa, 1)
        der_blob = pkey.as_der()
        #A quick but not thorough sanity check
        assert len(der_blob) == 92

    def test_size(self):
        rsa = RSA.gen_key(512, 3, callback=self._gen_callback)
        pkey = EVP.PKey()
        pkey.assign_rsa(rsa)
        size = pkey.size() 
        assert size == 64
        
    def test_hmac(self):
        assert util.octx_to_num(EVP.hmac('key', 'data')) == 92800611269186718152770431077867383126636491933, util.octx_to_num(EVP.hmac('key', 'data'))
        assert util.octx_to_num(EVP.hmac('key', 'data', algo='md5')) == 209168838103121722341657216703105225176, util.octx_to_num(EVP.hmac('key', 'data', algo='md5'))
        assert util.octx_to_num(EVP.hmac('key', 'data', algo='ripemd160')) == 1176807136224664126629105846386432860355826868536, util.octx_to_num(EVP.hmac('key', 'data', algo='ripemd160'))
        
        if m2.OPENSSL_VERSION_NUMBER >= 0x90800F:
            assert util.octx_to_num(EVP.hmac('key', 'data', algo='sha224')) == 2660082265842109788381286338540662430962855478412025487066970872635, util.octx_to_num(EVP.hmac('key', 'data', algo='sha224'))
            assert util.octx_to_num(EVP.hmac('key', 'data', algo='sha256')) == 36273358097036101702192658888336808701031275731906771612800928188662823394256, util.octx_to_num(EVP.hmac('key', 'data', algo='sha256'))
            assert util.octx_to_num(EVP.hmac('key', 'data', algo='sha384')) == 30471069101236165765942696708481556386452105164815350204559050657318908408184002707969468421951222432574647369766282, util.octx_to_num(EVP.hmac('key', 'data', algo='sha384'))
            assert util.octx_to_num(EVP.hmac('key', 'data', algo='sha512')) == 3160730054100700080556942280820129108466291087966635156623014063982211353635774277148932854680195471287740489442390820077884317620321797003323909388868696, util.octx_to_num(EVP.hmac('key', 'data', algo='sha512'))
        
        self.assertRaises(ValueError, EVP.hmac, 'key', 'data', algo='sha513')


    def test_get_rsa(self):
        """
        Testing retrieving the RSA key from the PKey instance.
        """
        rsa = RSA.gen_key(512, 3, callback=self._gen_callback)
        assert isinstance(rsa, RSA.RSA)
        pkey = EVP.PKey()
        pkey.assign_rsa(rsa) 
        rsa2 = pkey.get_rsa()
        assert isinstance(rsa2, RSA.RSA_pub)
        assert rsa.e == rsa2.e
        assert rsa.n == rsa2.n
        pem = rsa.as_pem(callback=self._pass_callback)
        pem2 = rsa2.as_pem()
        assert pem
        assert pem2
        assert pem != pem2
        
        message = "This is the message string"
        digest = sha.sha(message).digest()
        assert rsa.sign(digest) == rsa2.sign(digest)
        
        rsa3 = RSA.gen_key(512, 3, callback=self._gen_callback)
        assert rsa.sign(digest) != rsa3.sign(digest)
    
    def test_get_rsa_fail(self):
        """
        Testing trying to retrieve the RSA key from the PKey instance
        when it is not holding a RSA Key. Should raise a ValueError.
        """
        pkey = EVP.PKey()
        self.assertRaises(ValueError, pkey.get_rsa)

    def test_get_modulus(self):
        pkey = EVP.PKey()
        self.assertRaises(ValueError, pkey.get_modulus)

        rsa = RSA.gen_key(512, 3, callback=self._gen_callback)
        pkey.assign_rsa(rsa)
        mod = pkey.get_modulus()
        assert len(mod) > 0, mod
        assert len(mod.strip('0123456789ABCDEF')) == 0
        
    def test_verify_final(self):
        from M2Crypto import X509
        pkey = EVP.load_key('tests/signer_key.pem')
        pkey.sign_init()
        pkey.sign_update('test  message')
        sig = pkey.sign_final()
        
        # OK
        x509 = X509.load_cert('tests/signer.pem')
        pubkey = x509.get_pubkey()
        pubkey.verify_init()
        pubkey.verify_update('test  message')
        assert pubkey.verify_final(sig) == 1
        
        # wrong cert
        x509 = X509.load_cert('tests/x509.pem')
        pubkey = x509.get_pubkey()
        pubkey.verify_init()
        pubkey.verify_update('test  message')
        assert pubkey.verify_final(sig) == 0
        
        # wrong message
        x509 = X509.load_cert('tests/signer.pem')
        pubkey = x509.get_pubkey()
        pubkey.verify_init()
        pubkey.verify_update('test  message not')
        assert pubkey.verify_final(sig) == 0


class CipherTestCase(unittest.TestCase):
    def cipher_filter(self, cipher, inf, outf):
        while 1:
            buf=inf.read()
            if not buf:
                break
            outf.write(cipher.update(buf))
        outf.write(cipher.final())
        return outf.getvalue()

    def try_algo(self, algo):
        enc = 1
        dec = 0
        otxt='against stupidity the gods themselves contend in vain'
    
        k=EVP.Cipher(algo, 'goethe','12345678', enc, 1, 'sha1', 'saltsalt', 5)
        pbuf=cStringIO.StringIO(otxt)
        cbuf=cStringIO.StringIO()
        ctxt=self.cipher_filter(k, pbuf, cbuf)
        pbuf.close()
        cbuf.close()
    
        j=EVP.Cipher(algo, 'goethe','12345678', dec, 1, 'sha1', 'saltsalt', 5)
        pbuf=cStringIO.StringIO()
        cbuf=cStringIO.StringIO(ctxt)
        ptxt=self.cipher_filter(j, cbuf, pbuf)
        pbuf.close()
        cbuf.close()
    
        assert otxt == ptxt, '%s algorithm cipher test failed' % algo
        
    def test_ciphers(self):
        ciphers=['bf_ecb', 'bf_cbc', 'bf_cfb', 'bf_ofb',\
            #'idea_ecb', 'idea_cbc', 'idea_cfb', 'idea_ofb',\
            'cast5_ecb', 'cast5_cbc', 'cast5_cfb', 'cast5_ofb',\
            #'rc5_ecb', 'rc5_cbc', 'rc5_cfb', 'rc5_ofb',\
            'des_ecb', 'des_cbc', 'des_cfb', 'des_ofb',\
            'des_ede_ecb', 'des_ede_cbc', 'des_ede_cfb', 'des_ede_ofb',\
            'des_ede3_ecb', 'des_ede3_cbc', 'des_ede3_cfb', 'des_ede3_ofb',\
            'aes_128_ecb', 'aes_128_cbc', 'aes_128_cfb', 'aes_128_ofb',\
            'aes_192_ecb', 'aes_192_cbc', 'aes_192_cfb', 'aes_192_ofb',\
            'aes_256_ecb', 'aes_256_cbc', 'aes_256_cfb', 'aes_256_ofb',\
            'rc4', 'rc2_40_cbc']
        for i in ciphers:
            self.try_algo(i)

        self.assertRaises(ValueError, self.try_algo, 'nosuchalgo4567')
        
    def test_AES(self):
        enc = 1
        dec = 0
        tests = [
            # test vectors from rfc 3602
            #Case #1: Encrypting 16 bytes (1 block) using AES-CBC with 128-bit key
            {
            'KEY': '06a9214036b8a15b512e03d534120006',
            'IV':  '3dafba429d9eb430b422da802c9fac41',
            'PT':  'Single block msg',
            'CT':  'e353779c1079aeb82708942dbe77181a',
            },
            
            #Case #2: Encrypting 32 bytes (2 blocks) using AES-CBC with 128-bit key
            {
            'KEY': 'c286696d887c9aa0611bbb3e2025a45a',
            'IV':  '562e17996d093d28ddb3ba695a2e6f58',
            'PT':  unhexlify('000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f'),
            'CT':  'd296cd94c2cccf8a3a863028b5e1dc0a7586602d253cfff91b8266bea6d61ab1',
            },
            
            #Case #3: Encrypting 48 bytes (3 blocks) using AES-CBC with 128-bit key
            {
            'KEY': '6c3ea0477630ce21a2ce334aa746c2cd',
            'IV':  'c782dc4c098c66cbd9cd27d825682c81',
            'PT':  'This is a 48-byte message (exactly 3 AES blocks)',
            'CT':  'd0a02b3836451753d493665d33f0e8862dea54cdb293abc7506939276772f8d5021c19216bad525c8579695d83ba2684',
            },
        ]
        
        for test in tests:
            # encrypt
            k=EVP.Cipher(alg='aes_128_cbc', key=unhexlify(test['KEY']), iv=unhexlify(test['IV']), op=enc)
            pbuf=cStringIO.StringIO(test['PT'])
            cbuf=cStringIO.StringIO()
            ciphertext = hexlify(self.cipher_filter(k, pbuf, cbuf))
            cipherpadding = ciphertext[len(test['PT']) * 2:]
            ciphertext = ciphertext[:len(test['PT']) * 2] # Remove the padding from the end
            pbuf.close()
            cbuf.close()
            self.assertEqual(ciphertext, test['CT'])

            # decrypt
            j=EVP.Cipher(alg='aes_128_cbc', key=unhexlify(test['KEY']), iv=unhexlify(test['IV']), op=dec)
            pbuf=cStringIO.StringIO()
            cbuf=cStringIO.StringIO(unhexlify(test['CT'] + cipherpadding))
            plaintext=self.cipher_filter(j, cbuf, pbuf)
            pbuf.close()
            cbuf.close()
            self.assertEqual(plaintext, test['PT'])


    def test_raises(self):
        def _cipherFilter(cipher, inf, outf):
            while 1:
                buf = inf.read()
                if not buf:
                    break
                outf.write(cipher.update(buf))
            outf.write(cipher.final())
            return outf.getvalue()

        def decrypt(ciphertext, key, iv, alg='aes_256_cbc'):
            cipher = EVP.Cipher(alg=alg, key=key, iv=iv, op=0)
            pbuf = cStringIO.StringIO()
            cbuf = cStringIO.StringIO(ciphertext)
            plaintext = _cipherFilter(cipher, cbuf, pbuf)
            pbuf.close()
            cbuf.close()
            return plaintext
        
        self.assertRaises(EVP.EVPError, decrypt,
                          unhexlify('941d3647a642fab26d9f99a195098b91252c652d07235b9db35758c401627711724637648e45cad0f1121751a1240a4134998cfdf3c4a95c72de2a2444de3f9e40d881d7f205630b0d8ce142fdaebd8d7fbab2aea3dc47f5f29a0e9b55aae59222671d8e2877e1fb5cd8ef1c427027e0'),
                          unhexlify('5f2cc54067f779f74d3cf1f78c735aec404c8c3a4aaaa02eb1946f595ea4cddb'),
                          unhexlify('0001efa4bd154ee415b9413a421cedf04359fff945a30e7c115465b1c780a85b65c0e45c'))

        self.assertRaises(EVP.EVPError, decrypt,
                          unhexlify('a78a510416c1a6f1b48077cc9eeb4287dcf8c5d3179ef80136c18876d774570d'),
                          unhexlify('5cd148eeaf680d4ff933aed83009cad4110162f53ef89fd44fad09611b0524d4'),
                          unhexlify(''))


class PBKDF2TestCase(unittest.TestCase):
    def test_rfc3211_test_vectors(self):
        from binascii import hexlify, unhexlify
        
        password = 'password'
        salt = unhexlify('12 34 56 78 78 56 34 12'.replace(' ', ''))
        iter = 5
        keylen = 8
        ret = EVP.pbkdf2(password, salt, iter, keylen)
        self.assertEqual(hexlify(ret), 'D1 DA A7 86 15 F2 87 E6'.replace(' ', '').lower())
        
        password = 'All n-entities must communicate with other n-entities via n-1 entiteeheehees'
        salt = unhexlify('12 34 56 78 78 56 34 12'.replace(' ', ''))
        iter = 500
        keylen = 16
        ret = EVP.pbkdf2(password, salt, iter, keylen)
        self.assertEqual(hexlify(ret), '6A 89 70 BF 68 C9 2C AE A8 4A 8D F2 85 10 85 86'.replace(' ', '').lower())
        

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(EVPTestCase))
    suite.addTest(unittest.makeSuite(CipherTestCase))
    suite.addTest(unittest.makeSuite(PBKDF2TestCase))
    return suite    

if __name__ == '__main__':
    Rand.load_file('randpool.dat', -1) 
    unittest.TextTestRunner().run(suite())
    Rand.save_file('randpool.dat')

