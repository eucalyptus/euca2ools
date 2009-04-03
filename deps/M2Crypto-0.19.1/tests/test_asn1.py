#!/usr/bin/env python

"""Unit tests for M2Crypto.ASN1.

Copyright (c) 2005 Open Source Applications Foundation. All rights reserved."""

import unittest, time
from M2Crypto import ASN1, m2

class ASN1TestCase(unittest.TestCase):

    def test_Integer(self):
        pass # XXX Dunno how to test

    def test_BitSTring(self):
        pass # XXX Dunno how to test

    def test_String(self):
        asn1ptr = m2.asn1_string_new()
        text = 'hello there'
        # In RFC2253 format:
        # #040B68656C6C6F207468657265
        #      h e l l o   t h e r e 
        m2.asn1_string_set(asn1ptr, text)
        a = ASN1.ASN1_String(asn1ptr, 1)
        assert a.as_text() == 'hello there', a.as_text()
        assert a.as_text(flags=m2.ASN1_STRFLGS_RFC2253) == '#040B68656C6C6F207468657265', a.as_text(flags=m2.ASN1_STRFLGS_RFC2253)

    def test_Object(self):
        pass # XXX Dunno how to test

    def test_UTCTIME(self):
        asn1 = ASN1.ASN1_UTCTIME()
        assert str(asn1) == 'Bad time value'
        
        format = '%b %d %H:%M:%S %Y GMT'
        utcformat = '%y%m%d%H%M%SZ'

        s = '990807053011Z'
        asn1.set_string(s)
        #assert str(asn1) == 'Aug  7 05:30:11 1999 GMT'
        t1 = time.strptime(str(asn1), format)
        t2 = time.strptime(s, utcformat)
        assert t1 == t2
        
        asn1.set_time(500)
        #assert str(asn1) == 'Jan  1 00:08:20 1970 GMT'
        t1 = time.strftime(format, time.strptime(str(asn1), format))
        t2 = time.strftime(format, time.gmtime(500))
        assert t1 == t2
        
        t = long(time.time()) + time.timezone
        asn1.set_time(t)
        t1 = time.strftime(format, time.strptime(str(asn1), format))
        t2 = time.strftime(format, time.gmtime(t))
        assert t1 == t2
         

def suite():
    return unittest.makeSuite(ASN1TestCase)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())

