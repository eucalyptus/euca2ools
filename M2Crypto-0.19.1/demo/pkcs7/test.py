from M2Crypto import BIO, SMIME

pf = BIO.openfile('pkcs7-thawte.pem')
p7 = SMIME.load_pkcs7_bio(pf)
print p7.type(1)

