#!/usr/bin/env python
#
#vim: ts=4 sw=4 nowrap
#

"""PKI demo by Peter Teniz <peter.teniz@inverisa.net>"""

import M2Crypto


MBSTRING_FLAG = 0x1000
MBSTRING_ASC  = MBSTRING_FLAG | 1
MBSTRING_BMP  = MBSTRING_FLAG | 2


class Cert:
	def __init__ ( self ):
		self.RsaKey = { 'KeyLength'       : 1024,
						'PubExponent'     : 0x10001,		# -> 65537
						'keygen_callback' : self.callback 
					  }

		self.KeyPair         = None
		self.PKey            = None

		self.X509Request     = None 
		self.X509Certificate = None

	def callback ( self, *args ):
		return 'p'



	def CreatePKey ( self ):
		self.KeyPair = M2Crypto.RSA.gen_key( self.RsaKey['KeyLength'], self.RsaKey['PubExponent'], self.RsaKey['keygen_callback'] )
		#PubKey = M2Crypto.RSA.new_pub_key( self.KeyPair.pub () )

		self.KeyPair.save_key( 'KeyPair.pem', cipher='des_ede3_cbc', callback=self.callback )
		
		self.PKey = M2Crypto.EVP.PKey ( md='sha1')
		self.PKey.assign_rsa ( self.KeyPair )


	def CreateX509Request ( self ):
		#
		# X509 REQUEST
		#

		self.X509Request = M2Crypto.X509.Request ()

		#
		# subject
		#

		X509Name = M2Crypto.X509.X509_Name ()

		X509Name.add_entry_by_txt ( field='C',            type=MBSTRING_ASC, entry='austria',               len=-1, loc=-1, set=0 )    # country name
		X509Name.add_entry_by_txt ( field='SP',           type=MBSTRING_ASC, entry='kernten',               len=-1, loc=-1, set=0 )    # state of province name
		X509Name.add_entry_by_txt ( field='L',            type=MBSTRING_ASC, entry='stgallen',              len=-1, loc=-1, set=0 )    # locality name
		X509Name.add_entry_by_txt ( field='O',            type=MBSTRING_ASC, entry='labor',                 len=-1, loc=-1, set=0 )    # organization name
		X509Name.add_entry_by_txt ( field='OU',           type=MBSTRING_ASC, entry='it-department',         len=-1, loc=-1, set=0 )    # organizational unit name
		X509Name.add_entry_by_txt ( field='CN',           type=MBSTRING_ASC, entry='Certificate client',    len=-1, loc=-1, set=0 )    # common name
		X509Name.add_entry_by_txt ( field='Email',        type=MBSTRING_ASC, entry='user@localhost',        len=-1, loc=-1, set=0 )    # pkcs9 email address
		X509Name.add_entry_by_txt ( field='emailAddress', type=MBSTRING_ASC, entry='user@localhost',        len=-1, loc=-1, set=0 )    # pkcs9 email address     

		self.X509Request.set_subject_name( X509Name )

		#
		# publickey
		#

		self.X509Request.set_pubkey ( pkey=self.PKey )
		self.X509Request.sign ( pkey=self.PKey, md='sha1' )
		#print X509Request.as_text ()






	def CreateX509Certificate ( self ):
		#
		# X509 CERTIFICATE
		#

		self.X509Certificate =  M2Crypto.X509.X509 ()

		#
		# version
		#

		self.X509Certificate.set_version ( 0 )

		#
		# time notBefore
		#

		ASN1 = M2Crypto.ASN1.ASN1_UTCTIME ()
		ASN1.set_time ( 500 )
		self.X509Certificate.set_not_before( ASN1 )

		#
		# time notAfter
		#

		ASN1 = M2Crypto.ASN1.ASN1_UTCTIME ()
		ASN1.set_time ( 500 )
		self.X509Certificate.set_not_after( ASN1 )

		#
		# public key
		#

		self.X509Certificate.set_pubkey ( pkey=self.PKey )
		
		#
		# subject
		#

		X509Name = self.X509Request.get_subject ()

		#print X509Name.entry_count ()
		#print X509Name.as_text ()

		self.X509Certificate.set_subject_name( X509Name )

		#
		# issuer
		#

		X509Name = M2Crypto.X509.X509_Name ( M2Crypto.m2.x509_name_new () )

		X509Name.add_entry_by_txt ( field='C',            type=MBSTRING_ASC, entry='germany',               len=-1, loc=-1, set=0 )    # country name
		X509Name.add_entry_by_txt ( field='SP',           type=MBSTRING_ASC, entry='bavaria',               len=-1, loc=-1, set=0 )    # state of province name
		X509Name.add_entry_by_txt ( field='L',            type=MBSTRING_ASC, entry='munich',                len=-1, loc=-1, set=0 )    # locality name
		X509Name.add_entry_by_txt ( field='O',            type=MBSTRING_ASC, entry='sbs',                   len=-1, loc=-1, set=0 )    # organization name
		X509Name.add_entry_by_txt ( field='OU',           type=MBSTRING_ASC, entry='it-department',         len=-1, loc=-1, set=0 )    # organizational unit name
		X509Name.add_entry_by_txt ( field='CN',           type=MBSTRING_ASC, entry='Certificate Authority', len=-1, loc=-1, set=0 )    # common name
		X509Name.add_entry_by_txt ( field='Email',        type=MBSTRING_ASC, entry='admin@localhost',       len=-1, loc=-1, set=0 )    # pkcs9 email address
		X509Name.add_entry_by_txt ( field='emailAddress', type=MBSTRING_ASC, entry='admin@localhost',       len=-1, loc=-1, set=0 )    # pkcs9 email address     

		#print X509Name.entry_count ()
		#print X509Name.as_text ()

		self.X509Certificate.set_issuer_name( X509Name )

		#
		# signing
		#

		self.X509Certificate.sign( pkey=self.PKey, md='sha1' )
		print self.X509Certificate.as_text ()





if __name__ == '__main__':
	run = Cert ()
	run.CreatePKey ()
	run.CreateX509Request ()
	run.CreateX509Certificate ()
