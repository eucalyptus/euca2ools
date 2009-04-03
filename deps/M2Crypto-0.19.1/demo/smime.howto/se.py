#!/usr/bin/env python

"""S/MIME HOWTO demo program.

Copyright (c) 1999-2001 Ng Pheng Siong. All rights reserved."""

from M2Crypto import BIO, Rand, SMIME, X509

def makebuf(text):
    return BIO.MemoryBuffer(text)

# Make a MemoryBuffer of the message.
buf = makebuf('a sign of our times')

# Seed the PRNG.
Rand.load_file('randpool.dat', -1)

# Instantiate an SMIME object.
s = SMIME.SMIME()

# Load signer's key and cert. Sign the buffer.
s.load_key('signer_key.pem', 'signer.pem')
p7 = s.sign(buf)

# Load target cert to encrypt the signed message to.
x509 = X509.load_cert('recipient.pem')
sk = X509.X509_Stack()
sk.push(x509)
s.set_x509_stack(sk)

# Set cipher: 3-key triple-DES in CBC mode.
s.set_cipher(SMIME.Cipher('des_ede3_cbc'))

# Create a temporary buffer.
tmp = BIO.MemoryBuffer()

# Write the signed message into the temporary buffer.
s.write(tmp, p7)

# Encrypt the temporary buffer.
p7 = s.encrypt(tmp)
    
# Output p7 in mail-friendly format.
out = BIO.MemoryBuffer()
out.write('From: sender@example.dom\n')
out.write('To: recipient@example.dom\n')
out.write('Subject: M2Crypto S/MIME testing\n')
s.write(out, p7)

print out.read()

# Save the PRNG's state.
Rand.save_file('randpool.dat')

