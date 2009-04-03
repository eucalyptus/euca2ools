#!/usr/bin/env python
"""
Small utility to convert the Mozilla-format certificates
(/mozilla/security/nss/lib/ckfw/builtins/certdata.txt in the Mozilla CVS)
into PEM. Got the idea from http://curl.haxx.se/docs/parse-certs.txt.

Copyright (c) 2007 Open Source Applications Foundation.
"""

import array
from M2Crypto import X509

counter = 0
value = None
name = None

out = open('cacert.pem', 'wb')

for line in open('certdata.txt'):
    line = line.strip()
    if line.startswith('CKA_LABEL'):
        assert value is None

        label_encoding, name, dummy = line.split('"')
        label, encoding = label_encoding.split()

        assert encoding == 'UTF8'

    elif line == 'CKA_VALUE MULTILINE_OCTAL':
        assert name is not None

        value = array.array('c')

    elif value is not None and line == 'END':
        assert name is not None

        print 'Writing ' + name
        x509 = X509.load_cert_string(value.tostring(), X509.FORMAT_DER)
        if not x509.verify():
            print '  Skipping ' + name + ' since it does not verify'
            name = None
            value = None
            continue
        counter += 1

        out.write(name + '\n' + '=' * len(name) + '\n\n')
        out.write('SHA1 Fingerprint=' + x509.get_fingerprint('sha1') + '\n')
        out.write(x509.as_text())
        out.write(x509.as_pem())
        out.write('\n')

        name = None
        value = None

    elif value is not None:
        assert name is not None

        for number in line.split('\\'):
            if not number:
                continue

            value.append(chr(int(number, 8)))

print 'Wrote %d certificates' % counter
