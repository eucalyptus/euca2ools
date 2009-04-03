"""ZSmime.SmimeTag

Copyright (c) 1999-2001 Ng Pheng Siong. All rights reserved.
This software is released under the ZPL. Usual disclaimers apply."""

__version__ = '1.2'

# Zope tag stuff.
from DocumentTemplate.DT_String import String
from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_Var import Var, Call

# M2Crypto.
from M2Crypto import BIO, SMIME, X509

SmimeError = "SmimeTag Error"

class SmimeTag:
    """<dtml-smime>"""

    name = 'smime'
    blockContinuations = ()

    def __init__(self, blocks):
        tname, args, section = blocks[0]
        self.section = section

        args = parse_params(args, signer=None, recipients=None)
        has_key = args.has_key

        if has_key('signer'):
            self.signer = args['signer']
            try:
                Call(self.signer)
            except ParseError:
                raise SmimeError, ('Invalid parameter "signer".')
        else:
            raise SmimeError, ('The parameter "signer" was not specified in tag.')

        if has_key('recipients'):
            self.recipients = args['recipients']
            try:
                Call(self.recipients)
            except ParseError:
                raise SmimeError, ('Invalid parameter "recipients".')
        else:
            raise SmimeError, ('The parameter "recipients" was not specified in tag.')


    def render(self, md):
        # Render the dtml block.
        data = render_blocks(self.section.blocks, md)
        data_bio = BIO.MemoryBuffer(data)

        # Prepare to S/MIME.
        s = SMIME.SMIME()

        # Render the signer key, load into BIO. 
        try:
            signer = Var(self.signer).render(md)
        except ParseError:
            raise SmimeError, ('Invalid parameter "signer".')
        signer_key_bio = BIO.MemoryBuffer(signer)
        signer_cert_bio = BIO.MemoryBuffer(signer) # XXX Kludge.
        
        # Sign the data.
        s.load_key_bio(signer_key_bio, signer_cert_bio)
        p7 = s.sign(data_bio, flags=SMIME.PKCS7_TEXT)

        # Recreate coz sign() has consumed the MemoryBuffer.
        # May be cheaper to seek to start.
        data_bio = BIO.MemoryBuffer(data)

        # Render recipients, load into BIO.
        try:
            recip = Var(self.recipients).render(md)
        except ParseError:
            raise SmimeError, ('Invalid parameter "recipients".')
        recip_bio = BIO.MemoryBuffer(recip)

        # Load recipient certificates.
        sk = X509.X509_Stack()
        sk.push(X509.load_cert_bio(recip_bio))
        s.set_x509_stack(sk)

        # Set a cipher.
        s.set_cipher(SMIME.Cipher('des_ede3_cbc'))

        # Encrypt.
        tmp_bio = BIO.MemoryBuffer()
        s.write(tmp_bio, p7)
        p7 = s.encrypt(tmp_bio)

        # Finally, return the now signed/encrypted PKCS7.
        out = BIO.MemoryBuffer()
        s.write(out, p7)
        return out.getvalue()


    __call__ = render


String.commands['smime'] = SmimeTag

