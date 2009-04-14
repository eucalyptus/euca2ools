#!/usr/bin/env python
# XXX memory leaks
"""
    Unit tests for M2Crypto.EC, the curves
    
    There are several ways one could unittest elliptical curves
    but we are going to only validate that we are using the 
    OpenSSL curve and that it works with ECDSA.  We will assume
    OpenSSL has validated the curves themselves.  
    
    Also, some curves are shorter than a SHA-1 digest of 160 
    bits.  To keep the testing simple, we will take advantage
    of ECDSA's ability to sign any digest length and create a 
    digset string of only 48 bits.  Remember we are testing our
    ability to access the curve, not ECDSA itself.
    
    Copyright (c) 2006 Larry Bugbee. All rights reserved.
    
"""

import unittest
#import sha
from M2Crypto import EC, Rand
from test_ecdsa import ECDSATestCase as ECDSATest


curves = [
    ('secp112r1', 112),
    ('secp112r2', 112),
    ('secp128r1', 128),
    ('secp128r2', 128),
    ('secp160k1', 160),
    ('secp160r1', 160),
    ('secp160r2', 160),
    ('secp192k1', 192),
    ('secp224k1', 224),
    ('secp224r1', 224),
    ('secp256k1', 256),
    ('secp384r1', 384),
    ('secp521r1', 521),
    
    ('sect113r1', 113),
    ('sect113r2', 113),
    ('sect131r1', 131),
    ('sect131r2', 131),
    ('sect163k1', 163),
    ('sect163r1', 163),
    ('sect163r2', 163),
    ('sect193r1', 193),
    ('sect193r2', 193),
    ('sect233k1', 233),
    ('sect233r1', 233),
    ('sect239k1', 239),
    ('sect283k1', 283),
    ('sect283r1', 283),
    ('sect409k1', 409),
    ('sect409r1', 409),
    ('sect571k1', 571),
    ('sect571r1', 571),
    
    ('X9_62_prime192v1', 192),
    ('X9_62_prime192v2', 192),
    ('X9_62_prime192v3', 192),
    ('X9_62_prime239v1', 239),
    ('X9_62_prime239v2', 239),
    ('X9_62_prime239v3', 239),
    ('X9_62_prime256v1', 256),
    
    ('X9_62_c2pnb163v1', 163),
    ('X9_62_c2pnb163v2', 163),
    ('X9_62_c2pnb163v3', 163),
    ('X9_62_c2pnb176v1', 176),
    ('X9_62_c2tnb191v1', 191),
    ('X9_62_c2tnb191v2', 191),
    ('X9_62_c2tnb191v3', 191),
    ('X9_62_c2pnb208w1', 208),
    ('X9_62_c2tnb239v1', 239),
    ('X9_62_c2tnb239v2', 239),
    ('X9_62_c2tnb239v3', 239),
    ('X9_62_c2pnb272w1', 272),
    ('X9_62_c2pnb304w1', 304),
    ('X9_62_c2tnb359v1', 359),
    ('X9_62_c2pnb368w1', 368),
    ('X9_62_c2tnb431r1', 431),
    
    ('wap_wsg_idm_ecid_wtls1', 113),
    ('wap_wsg_idm_ecid_wtls3', 163),
    ('wap_wsg_idm_ecid_wtls4', 113),
    ('wap_wsg_idm_ecid_wtls5', 163),
    ('wap_wsg_idm_ecid_wtls6', 112),
    ('wap_wsg_idm_ecid_wtls7', 160),
    ('wap_wsg_idm_ecid_wtls8', 112),
    ('wap_wsg_idm_ecid_wtls9', 160),
    ('wap_wsg_idm_ecid_wtls10', 233),
    ('wap_wsg_idm_ecid_wtls11', 233),
    ('wap_wsg_idm_ecid_wtls12', 224),
]

# The following two curves, according to OpenSSL, have a 
# "Questionable extension field!" and are not supported by 
# the OpenSSL inverse function.  ECError: no inverse.
# As such they cannot be used for signing.  They might, 
# however, be usable for encryption but that has not 
# been tested.  Until thir usefulness can be established,
# they are not supported at this time.
#curves2 = [
#    ('ipsec3', 155),
#    ('ipsec4', 185),
#]

class ECCurveTests(unittest.TestCase):
    #data = sha.sha('Kilroy was here!').digest()     # 160 bits
    data = "digest"     # keep short (48 bits) so lesser curves 
                        # will work...  ECDSA requires curve be 
                        # equal or longer than digest

    def genkey(self, curveName, curveLen):
        curve = getattr(EC, 'NID_'+curveName)
        ec = EC.gen_params(curve)
        assert len(ec) == curveLen
        ec.gen_key()
        assert  ec.check_key(), 'check_key() failure for "%s"' % curveName
        return ec

#    def check_ec_curves_genkey(self):        
#        for curveName, curveLen in curves2:
#            self.genkey(curveName, curveLen)
#
#        self.assertRaises(AttributeError, self.genkey, 
#                                          'nosuchcurve', 1)

    def sign_verify_ecdsa(self, curveName, curveLen):
        ec = self.genkey(curveName, curveLen)
        r, s = ec.sign_dsa(self.data)
        assert ec.verify_dsa(self.data, r, s)
        assert not ec.verify_dsa(self.data, s, r)            

    def test_ec_curves_ECDSA(self):
        for curveName, curveLen in curves:
            self.sign_verify_ecdsa(curveName, curveLen)

        self.assertRaises(AttributeError, self.sign_verify_ecdsa, 
                                          'nosuchcurve', 1)

#        for curveName, curveLen in curves2:
#            self.assertRaises(EC.ECError, self.sign_verify_ecdsa, 
#                              curveName, curveLen)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ECCurveTests))
    return suite


if __name__ == '__main__':
    Rand.load_file('randpool.dat', -1) 
    unittest.TextTestRunner().run(suite())
    Rand.save_file('randpool.dat')

