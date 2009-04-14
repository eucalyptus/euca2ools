#!/usr/bin/env python2
#
# vim: ts=4 sw=4 nowrap
#
# ChannelHandler
#   ReceiveChannel
#   SendChannel
#
# SocketDispatcher
#   Loop
#   Poll
#   ReadEvent
#   WriteEvent
#
import sys, re, time, thread, os
import getopt
import exceptions
import select
import string
import socket
import StringIO
import traceback


from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, ENOTCONN, ESHUTDOWN, EINTR, EISCONN

STDOUT = sys.stdout

IDstdin  = 0
IDstdout = 1
IDstderr = 2




class ExitNow (exceptions.Exception):
    pass


class AuthError(exceptions.Exception):
    def __init__ (self, msg):
        self.msg = msg
    def __str__ (self):
        return repr( self.msg )

#----------------------------------------------------------------
#
# Class Security Certification
#
#----------------------------------------------------------------
import M2Crypto
import random
import base64
import sha

class CertHandler:

    def __init__ ( self ):
        self.Nonce       = None
        self.CurrentObj  = {}
        #self.ServerName = socket.gethostbyaddr(socket.gethostname())[2][0]
        self.ServerName  = 'AuthInstance'

        self.ObjNames    = { 'C' : 'countryName', 'ST' : 'stateOrProvinceName', 'L' : 'localityName', 'O' : 'organizationName', 'OU' : 'organizationalUnitName',  'CN' : 'commonName', 'email' : 'emailAddress' }
        self.ObjMap      = {}

        self.Params     = { 'Digest'    : 'sha1',
                            'Version'   : 1,
                            'Serial'    : 1,
                            'NotBefore' : ( 60 * 60 * 24 * 365 ),
                            'NotAfter'  : ( 60 * 60 * 24 * 365 * 5 ),
                            'Issuer'    : { 'countryName' : 'US', 'stateOrProvinceName' : 'florida', 'localityName'  : 'tampas', 'organizationName' : 'watersprings', 'organizationalUnitName' : 'security', 'commonName' : 'Certificate Authority', 'emailAddress' : 'admin@security' },
                            'Subject'   : { 'countryName' : 'US', 'stateOrProvinceName' : 'florida', 'localityName'  : 'miami', 'organizationName' : 'watersprings', 'organizationalUnitName' : 'security', 'commonName' : 'Certificate Authority', 'emailAddress' : 'admin@security' }
                          }
        self.KeyEnv     = { 'RsaPubKey' : [ '-----BEGIN PUBLIC KEY-----', '-----END PUBLIC KEY-----' ],
                            'RsaPKey'   : [ '-----BEGIN RSA PRIVATE KEY-----', '-----END RSA PRIVATE KEY-----' ],
                            'X509Cert'  : [ '-----BEGIN CERTIFICATE-----', '-----END CERTIFICATE-----' ]
                          }
        self.CertContainer ()

        self.ObjFromContainer ( ObjName='CA' )
        self.ObjFromContainer ( ObjName=self.ServerName )
        self.ServerObj = self.ObjMap[ self.ServerName ]





    def CertContainer (self):
        self.PemMap     = { 'CA'            : { 'Subject'   : {'organizationalUnitName': 'security', 'organizationName': 'watersprings', 'commonName': 'Certificate Authority', 'stateOrProvinceName': 'florida', 'countryName': 'US', 'emailAddress': 'admin@security', 'localityName': 'miami'},
                                                'RsaPKey'   : ['MIICXQIBAAKBgQDmAl+4+XdF34D3kBN58An29mA8/D+NUHVJW+XeE96uDJ9mw8f1', 'xguVYgfpMaiVihW/qDWZRu/NhWOfheKBVNstx5OcqIjY10vBvGAG17CQZhcon8eN', 'Kufg7XzON7e5WXXD8qyklhuesHtTEGGpZ1FfA+n+D/0JF3YfTBDeYyY2VQIDAQAB', 'AoGBAI53L/Uxx7fmzUoJ2pZvoKxwRIHhuDd+e3c5zbJ1WjsyJFWRtLw9tBUOCFpf', 'YM1nHzt8I97RulzxXxiC5B45ghu3S0s+B06oEOUxNLbjsai08DKBRFqM+IZIx11r', 'IM/tZsTdJg1KtKojRu63NDtOzR6a7ggTeMge5CDKpXVWpvVtAkEA+QF/q2NnsdmL', 'ak6ALl8QwMbvwujJcjLwvecHQJmB0jO9KF60Hh4VY8mTRIMZ/r9Wf+REsQcZtmhG', 'WRr12si5qwJBAOx4R0Wd/inoXOpvKheIoKgTg01FnLhT8uiLY59CuZRr6AcTELjC', 'Kvk6LyfhspYBkUwWAEwKxJ3kMeqXG+k8z/8CQQCy+GDKzqe5LKMHxWRb7/galuG9', 'NZOUgQiHdYXA6JRmgMl0Op07CGRXVIqEs7X7Y4rIYUj99ByG/muRn88VcTABAkBQ', 'Z6V0WoBtp4DQhfP+BIr8G4Zt49miI4lY4OyC3qFTgk1m+miZKgyKqeoW2Xtr3iSV', 'hnWbZZ3tQgZnCfKHoBHpAkAmf2OvfhLxaW1PwdjBdm9tFGVbzkLFDqdqww2aHRUx', 'sXonHyVG2EDm37qW7nzmAqUgQCueMhHREZQYceDrtLLO'],
                                                'X509Cert'  : ['MIICpzCCAhCgAwIBAQIBATANBgkqhkiG9w0BAQUFADCBmTERMA8GA1UECxMIc2Vj', 'dXJpdHkxFTATBgNVBAoTDHdhdGVyc3ByaW5nczEeMBwGA1UEAxMVQ2VydGlmaWNh', 'dGUgQXV0aG9yaXR5MRAwDgYDVQQIEwdmbG9yaWRhMQswCQYDVQQGEwJVUzEdMBsG', 'CSqGSIb3DQEJARYOYWRtaW5Ac2VjdXJpdHkxDzANBgNVBAcTBnRhbXBhczAeFw0w', 'MzAzMzExMDQ2MDVaFw0wOTAzMjkxMDQ2MDVaMIGYMREwDwYDVQQLEwhzZWN1cml0', 'eTEVMBMGA1UEChMMd2F0ZXJzcHJpbmdzMR4wHAYDVQQDExVDZXJ0aWZpY2F0ZSBB', 'dXRob3JpdHkxEDAOBgNVBAgTB2Zsb3JpZGExCzAJBgNVBAYTAlVTMR0wGwYJKoZI', 'hvcNAQkBFg5hZG1pbkBzZWN1cml0eTEOMAwGA1UEBxMFbWlhbWkwgZ8wDQYJKoZI', 'hvcNAQEBBQADgY0AMIGJAoGBAOYCX7j5d0XfgPeQE3nwCfb2YDz8P41QdUlb5d4T', '3q4Mn2bDx/XGC5ViB+kxqJWKFb+oNZlG782FY5+F4oFU2y3Hk5yoiNjXS8G8YAbX', 'sJBmFyifx40q5+DtfM43t7lZdcPyrKSWG56we1MQYalnUV8D6f4P/QkXdh9MEN5j', 'JjZVAgMBAAEwDQYJKoZIhvcNAQEFBQADgYEAK7f4YodUnT7Ygp7BWBBDHSq/r+tY', 'H69ly3W23U5VupaIglNiNQoMqnZpVVfcuIYltajrux5TSH4gPbenCg163Ua8RvF6', 'E2JElccprbKiCf9tf8l6Rxpsall4EF+CazP56DiUD1NfGLhWp9V2ga9SoynEo1P1', 'eztMBfk01atBJ/s=']
                                              },
                            'AuthInstance'  : { 'Subject'   : {'commonName': 'AuthInstance', 'organizationalUnitName': 'security', 'emailAddress': 'ioclient@AuthInstance'},
                                                'RsaPKey'   : ['MIICXQIBAAKBgQCwfB6CoOQTJTd6D4ua1G/H9hwqpdVUMMjG3O8Y93vYGesZdwtT', '1iEQX/6TWACBxa7jOC8hHUHe2lsPu7imHv8dDiD59Rzets7BM88HsJTemYrxSv5G', 'uh8FloB1KEtSHeCZSlDT/tzSX4M0JfVPmtx+0FsyDOVZ6jXjRIyIKgqDlwIDAQAB', 'AoGAYc8YFatXW6j3mwU8iL2NidPC/nvTxAoZa+UL+dlG4JhUrFNGitsUjf+1ljFi', 'bomBiFod/Is7c2euqgSOrDpnheYlogv2QpnP80YUpiv9OruaB9I1zqJ7QM7PrkrH', 'm1C36DzyzVY+4DMvTV29do4Mf6CKT8xf6hXlLK/NbqwO9NkCQQDYwxwCTWxrkX08', '+0c5KaTYxfqCByxOqoiKl97p6wHxNtlzdLeFoSZD0n3Q1c2v0DIXhcBPRPPaZBWC', 'yTayMkRzAkEA0G6I5mHQVNIx18Xmc75urC0QWrum9cj5VcyRvl3KCzB2kQoXkx6v', 'y0JN6YS37rSp8vmvIFNO/oHWSuEJlFYfTQJAajWv07D8Hvj61JaLH4c4Lr9TL8M0', 'Apesr7wajaOJIBgwFFJsWh3MEg9hdqJMVok9AimXQUAX/DpuD9dn5Yib4QJBAIdt', 'Kno2V7ylDkmahk/yDcrFRPkPMD5GpOrAjnnYSqzWglNe8U5gA+zXWfQ+jZwFut7q', 'qIUiXBM1nVzttuGwy4kCQQC3MHppypSWoFqd+TaxK3MX/HoZqaoRELXdeiniOt3Z', 'gFMJ4m6D9lL4segWDoDpequjDYxv2cl+wS1+qDOyeG3J'],
                                                'X509Cert'  : ['MIIBxDCCAS2gAwIBAQIBATANBgkqhkiG9w0BAQUFADAAMB4XDTAzMDMzMTEwNTE1', 'N1oXDTA5MDMyOTEwNTE1N1owUDEkMCIGCSqGSIb3DQEJARYVaW9jbGllbnRAQXV0', 'aEluc3RhbmNlMREwDwYDVQQLEwhzZWN1cml0eTEVMBMGA1UEAxMMQXV0aEluc3Rh', 'bmNlMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCwfB6CoOQTJTd6D4ua1G/H', '9hwqpdVUMMjG3O8Y93vYGesZdwtT1iEQX/6TWACBxa7jOC8hHUHe2lsPu7imHv8d', 'DiD59Rzets7BM88HsJTemYrxSv5Guh8FloB1KEtSHeCZSlDT/tzSX4M0JfVPmtx+', '0FsyDOVZ6jXjRIyIKgqDlwIDAQABMA0GCSqGSIb3DQEBBQUAA4GBAFsXewlXnKpH', 'uSwxavmLPUqRk7o1D5E3ByTddBe3BY5NqEXk7Y2SJFtumiuUY5/sWB/aO8Xbqj/b', '/7Cwg9+bc9QqxeeIe/YvtFOmv1ELh2BC1Nof7zSa5rLa/+gPYCoogS4mLRMuUfRk', 'tVHhpoxL1B+UXp4jNeKeTgquOjpUiyBR']
                                              },
                            '192.168.1.20' : {  'Subject'   : {'commonName': '192.168.1.20', 'organizationalUnitName': 'security', 'emailAddress': 'ioclient@192.168.1.20'},
                                                'RsaPKey'   : ['MIICWwIBAAKBgQDD285BGY+FHhfpRvcqupN8X2lPwUNq4G7k5kit5cyuQLfN0+eQ', 'I+VFZdtfJhCZC54dEIvNgA4I7563pRUD0S9rmN6kh/M0GgrKZjYNO+CvvG2dts26', 'MGK0eUQaSsvDf9phEA+0mSv9dsUrdyBTJBn4mXvApekYHt+mNLfCVLkM1QIDAQAB', 'AoGAMqcFB3cJ0/59Zpowz/8ip3axcKvluJ1EcLRRtY+JyML6BiQ4beGqqLD38/qP', 'LlV/1bpyvXnRp2P5IztxXORbo77IzDVzl62YesQATnecSCMLTaeOusy2EZZsjE0k', 'V2cR1rZvzyJPY+Fi8X54hiB+5IcKkPRX9LVw7+yBbBh4sKECQQD0Yi0/DGa3IetR', '9F+/jgN/VIcTd5KwMBW3Bw/+Bh78ZlZGaucpRiR1IQuD7sLTnhNS6RMJUxv10jnS', 'BGW9pjX5AkEAzSslOGFyJ5Aoy48rgC2kKwq6nFKJ/PmY92cnm0nqmwb2npbOtDxz', 'sPUdb7oYmUU/nVCJh3yb+KJIw2g9XxnUvQJAG8ybNwPTH1vlZ+Izjhe6gB5+axF8', 'BzzBC5vrDstldPKzN7lraD+JYCWNKMndMbNWoWTP/IyOrqzmVOSZKjShCQJAbzuE', 'C2QxaqeqpmnxkKWuCrPfZl8NdryvpPolK/jQG8qTrHlgibD4nCjYE7nWGkrD6Xs/', 'hNgXC56YSnDaTRQJFQJAD5GFACv9QgcMZhy1hza0yGDMSQ0WR8/y3CJhi3DPOuAf', 'MetGM1kLQR8bDFrl7yEs+Nufk8QTsE5ngZ7dGFgmuA=='],
                                                'X509Cert'  : ['MIIBxDCCAS2gAwIBAQIBATANBgkqhkiG9w0BAQUFADAAMB4XDTAzMDMzMTEwNTMw', 'NVoXDTA5MDMyOTEwNTMwNVowUDEkMCIGCSqGSIb3DQEJARYVaW9jbGllbnRAMTky', 'LjE2OC4xLjIwMREwDwYDVQQLEwhzZWN1cml0eTEVMBMGA1UEAxMMMTkyLjE2OC4x', 'LjIwMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDD285BGY+FHhfpRvcqupN8', 'X2lPwUNq4G7k5kit5cyuQLfN0+eQI+VFZdtfJhCZC54dEIvNgA4I7563pRUD0S9r', 'mN6kh/M0GgrKZjYNO+CvvG2dts26MGK0eUQaSsvDf9phEA+0mSv9dsUrdyBTJBn4', 'mXvApekYHt+mNLfCVLkM1QIDAQABMA0GCSqGSIb3DQEBBQUAA4GBAA5pWiXJOHCJ', 'P6kHcBITJuwv94zZ0dbHby1ljUfG/8z3Fmr8JRUcTuTtgVYH9M0O9QujIR8YLWSV', '0GeD3nkLRn0+ezam0CW0dF/Ph5vNXFP4a0DSEVv7T0G21VFmbUV3xrVeaXARFuLa', 'AtqRoSyBMajd3g0WNXDCgGEH7LvzJ5EP']
                                              },
                            '192.168.1.26' : {  'Subject'   : {'commonName': '192.168.1.26', 'organizationalUnitName': 'security', 'emailAddress': 'ioclient@192.168.1.26'},
                                                'RsaPKey'   : ['MIICXQIBAAKBgQC5ILRHC3wFoqG9Egb96N3iGEnVrgvQikHyXYc/jFMUgB79rVJp', 'hY1MziGkSjSyc3RFMshkjHlMlARMPCNtomIikqAQaO4Eke2SYWyaOBoTdkeOy+yZ', 't/POpoGp3nRmKGed6NNcdMd5BO01GiatUb7X/Se3Yyvmj5UcEmv/hZQGFwIDAQAB', 'AoGBALdR5FMp0zE9X437iQLsErQuOwcmpzplfnJDHYfXK/nz+TxY4m/tuQNiZ7vp', 'Y4+Gdo+Dfx7aX89uD2dycd7B2wwTziBGIEjhusD8gtralVjhBDjCowSOkezWTeY+', '2h40NB4e1uypOZb0PXWvAL/l9xN7NBGioq9zmShT5c+FFO8RAkEA4k3QSaT1ScGI', '5II5JolvPnv6yS+0dCQTn1SC2ABWbH75NDUHMGAdNIf1sqhaLSQnY9GuXhb8XqX6', 'UUhoypUHzwJBANFrqnuEuTNKR0HVD31/2trPYLfZL6/9RUsR4mlvxPb0tX+T5LVL', '5he43zbura/lZqNxt0ZVeD03LanPN7bvZzkCQQCMAToIJa6+x6YKQOpchhA1pvwb', 'NZE9fQhKvT0JpwPQsak4/EmLSxsmYarGsdLANKrN3W4ztaLCZ4r6eIKkOhkPAkBz', 'ke4wYitucbRnUTRONuvJSx599x6JCcVey0zekO7qtlsfP7e8kVk2iDCu+QLjCj8d', 'Pdk9uFc1uSi7CH8ftniJAkBLNYF0kfGC+CaTuyfnIwiBZ/tjmm4UvHfwtlaZHJYc', 'QIjimBxVA7mujrv3xIBTiDMdxUhq9YIaKIEdlveaTwPK'],
                                                'X509Cert'  : ['MIIBxDCCAS2gAwIBAQIBATANBgkqhkiG9w0BAQUFADAAMB4XDTAzMDMzMTEwNTQx', 'NloXDTA5MDMyOTEwNTQxNlowUDEkMCIGCSqGSIb3DQEJARYVaW9jbGllbnRAMTky', 'LjE2OC4xLjI2MREwDwYDVQQLEwhzZWN1cml0eTEVMBMGA1UEAxMMMTkyLjE2OC4x', 'LjI2MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5ILRHC3wFoqG9Egb96N3i', 'GEnVrgvQikHyXYc/jFMUgB79rVJphY1MziGkSjSyc3RFMshkjHlMlARMPCNtomIi', 'kqAQaO4Eke2SYWyaOBoTdkeOy+yZt/POpoGp3nRmKGed6NNcdMd5BO01GiatUb7X', '/Se3Yyvmj5UcEmv/hZQGFwIDAQABMA0GCSqGSIb3DQEBBQUAA4GBAMPd5SXzpwZ+', '40SdOv/PeQ5cjieDm6QjndWE/T8nG2I5h6YRWbZPohsCClQjrTyZCMXwcUiCimuJ', 'BaMigI/YqP5THVv58Gu8DpoVZppz7uhUNS5hsuV9lxZUh1bRkUtL6n0qSTEdM34I', 'NJBJKGlf0skULg9BT4LJYTPGWJ0KosUl']
                                              }
                          }

    def CreateObj ( self, ObjName='CA' ):
        self.ObjMap[ObjName]   = {  'RsaPKey'    : None,
                                    'PsaPubKey'  : None,
                                    'EvpPKey'    : None,
                                    'EvpPubKey'  : None,
                                    'X509Req'    : None,
                                    'X509Cert'   : None,
                                }
        self.CurrentObj = self.ObjMap[ObjName]

    def ObjFromContainer (self, ObjName='CA' ):
        if not self.ObjMap.has_key( ObjName ):
            self.CreateObj ( ObjName=ObjName )
            self.PKeyFromPemRepr ( ObjName=ObjName )
            self.CertFromPemRepr ( ObjName=ObjName )

    def PKeyFromPemRepr ( self, ObjName=None, PemPKey=None ):
        def callback (): return ''
        if self.PemMap.has_key( ObjName ):
            UsedPemPKey = self.KeyEnv['RsaPKey'][0] + '\n' + string.join( self.PemMap[ObjName]['RsaPKey'], '\n' ) + '\n' + self.KeyEnv['RsaPKey'][1] + '\n'
        else:
            if not PemPKey:
                raise AuthError( 'no such Object "%s" in container - abort!' % ObjName )
            else:
                UsedPemPKey = PemPKey
        self.CurrentObj['RsaPKey']   = M2Crypto.RSA.load_key_string( UsedPemPKey, callback )
        self.CurrentObj['EvpPKey']   = M2Crypto.EVP.PKey ( md='sha1' )
        self.CurrentObj['EvpPKey'].assign_rsa ( self.CurrentObj['RsaPKey'] )
        self.CurrentObj['RsaPubKey'] = M2Crypto.RSA.new_pub_key( self.CurrentObj['RsaPKey'].pub () )
        
    def CertFromPemRepr ( self, ObjName=None, PemCert=None ):
        if self.PemMap.has_key( ObjName ):
            UsedPemCert = self.KeyEnv['X509Cert'][0] + '\n' + string.join( self.PemMap[ObjName]['X509Cert'], '\n' ) + '\n' + self.KeyEnv['X509Cert'][1] + '\n'
        else:
            UsedPemCert = PemCert
        self.CurrentObj['X509Cert']  = M2Crypto.X509.load_cert_string( PemCert )
        self.CurrentObj['EvpPubKey'] = self.CurrentObj['X509Cert'].get_pubkey ()
        #self.CurrentObj['RsaPubKey'] = M2Crypto.RSA.rsa_from_pkey( self.CurrentObj['EvpPubKey'] )

    def ObjNameFromPemCert ( self, PemCert=None ):
        """
        generate objmap structure and fill it with values from PemCert
        return ObjName string
        """
        X509Cert   = M2Crypto.X509.load_cert_string( PemCert )
        Subject    = X509Cert.get_subject ()
        SubjectTxt = Subject.print_ex ()
        SubjectTxtList = re.split('[\n\r]', SubjectTxt )
        SubjectMap = {}
        for Entry in SubjectTxtList:
            ( Key, Value ) = re.split('=', Entry)
            if self.ObjNames.has_key( Key ):
                SubjectMap[ self.ObjNames[Key] ] = Value
            else:
                SubjectMap[ Key ] = Value
        if not SubjectMap.has_key( 'commonName' ):
            return False
        ObjName = SubjectMap['commonName']
        if not self.ObjMap.has_key( ObjName ):
            self.CreateObj( ObjName=ObjName )
            self.CurrentObj = self.ObjMap[ObjName]
            self.CurrentObj['X509Cert']  = X509Cert
            self.CurrentObj['EvpPubKey'] = self.CurrentObj['X509Cert'].get_pubkey ()
            self.CurrentObj['RsaPubKey'] = M2Crypto.RSA.rsa_from_pkey( self.CurrentObj['EvpPubKey'] )
        else:
            self.CurrentObj = self.ObjMap[ ObjName ]
        return ObjName
        


    def ServerCert ( self ):
        self.ObjFromContainer( ObjName='X509Auth' )


    def CreatePKey ( self ):
        def PassPhraseFkt (): return ''
        RsaKeyParams    = { 'KeyLength'       : 1024,
                            'PubExponent'     : 0x10001,           # -> 65537
                            'keygen_callback' : PassPhraseFkt
                          }
        self.CurrentObj['RsaPKey'] = M2Crypto.RSA.gen_key( RsaKeyParams['KeyLength'], RsaKeyParams['PubExponent'], RsaKeyParams['keygen_callback'] )
        self.CurrentObj['EvpPKey'] = M2Crypto.EVP.PKey ( md=self.Params['Digest'] )
        self.CurrentObj['EvpPKey'].assign_rsa ( self.CurrentObj['RsaPKey'] )
        #print self.EvpPKey


    def CreateCert ( self, SignEvpPKey=None ):
        """
        generate new x509 certificate
        SignEvpKey    pkey to sign x509 certification, if None  this x509 cert will be self signed
        """
        self.CurrentObj = self.ObjMap['CA']
        self.CreatePKey ()
        X509Cert = M2Crypto.X509.X509 ()
        X509Cert.set_version ( self.Params['Version'] )
        X509Cert.set_serial_number ( self.Params['Serial'] )
        X509Cert.set_not_before ( int( time.time() - self.Params['NotBefore'] ))        # 1 year in the past
        X509Cert.set_not_after ( int( time.time() + self.Params['NotAfter'] ))          # 5 years in the future
        X509Cert.set_issuer ( self.Params['Issuer'] )
        X509Cert.set_subject ( self.Params['Subject'] )
        X509Cert.set_pubkey ( self.CurrentObj['EvpPKey'] )
        if SignEvpPKey:
            X509Cert.sign ( SignEvpPKey, self.Params['Digest'] )
        else:
            X509Cert.sign ( self.CurrentObj['EvpPKey'], self.Params['Digest'] )
        self.CurrentObj['X509Cert'] = X509Cert
        self.DumpOutInternalPemRepr( ObjName='CA' )


    def CreateObjCert (self, ObjName):
        """
        generate Obj with new PKey and Request, signed by 'CA'
        ObjName    the primary key to identify key-pair
        """
        # new obj
        if not self.ObjMap.has_key( ObjName ):
            self.ObjMap[ObjName] = {}
        self.CurrentObj = self.ObjMap[ObjName]
        if not self.CurrentObj.has_key( 'Subject' ):
            self.CurrentObj['Subject'] = { 'organizationalUnitName' : 'security', 'commonName' : ObjName, 'emailAddress' : 'ioclient@' + ObjName }
        # new pkey      
        self.CreatePKey ()
        # new request
        self.CreateReq ( SignEvpPKey=self.ObjMap['CA']['EvpPKey'] )
        # new certification
        if not self.Req2Cert ( SignEvpPKey=self.ObjMap['CA']['EvpPKey'] ):
            print "300 error occured while verifying - abort!"
        # shipout x509 certification
        self.DumpOutInternalPemRepr( ObjName=ObjName )


    def CreateReq ( self, SignEvpPKey=None ):
        X509Req = M2Crypto.X509.Request ()
        if self.Params['Version']:
            X509Req.set_version ( self.Params['Version'] )
        X509Req.set_subject ( self.CurrentObj['Subject'] )
        X509Req.set_pubkey ( self.CurrentObj['EvpPKey'] )
        if SignEvpPKey:
            X509Req.sign ( SignEvpPKey, self.Params['Digest'] )
        else:
            X509Req.sign ( self.CurrentObj['EvpPKey'], self.Params['Digest'] )
        self.CurrentObj['X509Req'] = X509Req


    def Req2Cert ( self, SignEvpPKey=None ):
        X509Cert = M2Crypto.X509.X509 ()
        Version = self.CurrentObj['X509Req'].get_version ()
        X509Cert.set_version ( Version )
        X509Cert.set_serial ( self.Params['Serial'] )
        X509Cert.set_not_before ( int( time.time() - self.Params['NotBefore'] ))        # 1 year in the past
        X509Cert.set_not_after ( int( time.time() + self.Params['NotAfter'] ))          # 5 years in the future
        Issuer = self.ObjMap['CA']['X509Cert'].get_issuer ()
        X509Cert.set_issuer_name ( Issuer )
        X509Name_Subject = self.CurrentObj['X509Req'].get_subject ()
        X509Cert.set_subject_name ( X509Name_Subject )
        PKey = self.CurrentObj['X509Req'].get_pubkey ()
        EvpPKey = M2Crypto.EVP.PKey( PKey )
        X509Cert.set_pubkey ( EvpPKey )
        if SignEvpPKey:
            X509Cert.sign ( SignEvpPKey, self.Params['Digest'] )
        else:
            X509Cert.sign ( self.CurrentObj['EvpPKey'], self.Params['Digest'] )
        self.CurrentObj['X509Cert'] = X509Cert
        if self.VerifyCert ( SignEvpPKey ):
            return True
        else:
            return False

        


    #--------------------------------
    # CertHandler  Verifying
    #--------------------------------
    def ExtractPublicKeyFromCert ( self ):
        self.CurrentObj['EvpPubKey'] = self.CurrentObj['X509Cert'].get_pubkey ()

    def VerifyCert ( self, EvpPKey ):
        if dir(EvpPKey).count('_ptr'):
            Result = self.CurrentObj['X509Cert'].verify ( EvpPKey._ptr() )
        else:
            Result = self.CurrentObj['X509Cert'].verify ( EvpPKey )
        if Result:
            return True
        return False



    #--------------------------------
    # CertHandler  DumpOut
    #--------------------------------
    def DumpOutInternalPemRepr( self, ObjName='unknown', File='PyReprPem.txt' ):
        if File:
            open( File, 'w').write("\t\t\t\t'%s' : { " % ( ObjName ))
        else:
            sys.stdout.write("\t\t\t\t'%s' : { " % ( ObjName ))
        self.ShowX509CertSubject ( File )
        self.RsaPKey2PemRepr ( File, Cipher=None )      # unprotectd pkey representation
        self.X509Cert2PemRepr ( File )
        if File:
            open( File, 'a').write("\t\t\t\t\t  }\n")
        else:
            sys.stdout.write("\t\t\t\t\t  }\n")

    def ShowX509CertIssuer ( self, File=None ):
        IssuerName = self.CurrentObj['X509Cert'].get_issuer ()
        print IssuerName.print_ex ()

    def ShowX509CertSubject ( self, File=None ):
        Subject = self.CurrentObj['X509Cert'].get_subject ()
        SubjectTxt = Subject.print_ex ()
        SubjectTxtList = re.split('[\n\r]', SubjectTxt )
        SubjectMap = {}
        for Entry in SubjectTxtList:
            ( Key, Value ) = re.split('=', Entry)
            if self.ObjNames.has_key( Key ):
                SubjectMap[ self.ObjNames[Key] ] = Value
            else:
                SubjectMap[ Key ] = Value
        if File:
            open( File, 'a').write("'Subject'    : %s,\n" % ( repr( SubjectMap ) ))
        else:
            sys.stdout.write("Subject: %s\n" % ( repr( SubjectMap ) ))

    def RsaPKey2PemRepr ( self, File=None, Cipher=None ):
        """
        converting pkey to PEM representation
        Cipher     if set to None, the pkey will be unprotected!!!!!   possible other value: 'des_ede3_cbc'
        """
        PemRsaPKey = self.CurrentObj['RsaPKey'].repr_key_pem ( cipher=Cipher )
        PemRsaPKeyList = re.split('[\n\r]', PemRsaPKey)
        if File:
            open( File, 'a').write("\t\t\t\t\t\t\t\t'RsaPKey'   : %s,\n" % ( repr(PemRsaPKeyList[1:-2]) ))
        else:
            sys.stdout.write("\t\t\t\t\t\t\t\t'RsaPKey'   : %s,\n" % ( repr(PemRsaPKeyList[1:-2]) ))

    def X509Cert2PemRepr ( self, File=None ):
        PemCert = self.CurrentObj['X509Cert'].repr_cert_pem ()
        #print PemCert
        PemCertList = re.split('[\n\r]', PemCert)
        if File:
            open( File, 'a').write("\t\t\t\t\t\t\t\t'X509Cert'  : %s\n" % ( repr(PemCertList[1:-2]) ))
        else:
            sys.stdout.write("\t\t\t\t\t\t\t\t'X509Cert'  : %s\n" % ( repr(PemCertList[1:-2]) ))



    #--------------------------------
    # CertHandler  encryption / decryption
    #--------------------------------
    def CreateNonce ( self ):
        """
        creating some randomised data
        return new Nonce string
        """
        random.seed ()
        RawNonce = "%s_%f_%f" % ( os.getpid(), time.time(), random.random() )
        sha1=M2Crypto.EVP.MessageDigest('sha1')
        sha1.update( RawNonce )
        NonceDecrypted = sha1.digest()
        return NonceDecrypted

    def NonceEncryptPrivate ( self, NonceDecrypted, RsaPKey=None ):
        """
        creating private encrypted string from NonceDecrypted
        """
        padding = M2Crypto.RSA.pkcs1_padding
        if not RsaPKey:
            UsedRsaPKey = self.ServerObj['RsaPKey']
        else:
            UsedRsaPKey = RsaPKey
        NoncePrivEncrypted = UsedRsaPKey.private_encrypt ( NonceDecrypted, padding )
        return NoncePrivEncrypted

    def NonceEncryptPublic ( self, NonceDecrypted, RsaPubKey=None ):
        """
        creating public encrypted string from NonceDecrypted
        """
        padding = M2Crypto.RSA.pkcs1_padding
        if not RsaPubKey:
            UsedRsaPubKey = self.ServerObj['RsaPubKey']
        else:
            UsedRsaPubKey = RsaPubKey
        NoncePubEncrypted = UsedRsaPubKey.public_encrypt ( NonceDecrypted, padding )
        return NoncePubEncrypted

    def NonceDecryptPublic ( self, NoncePrivEncrypted, RsaPubKey=None ):
        """
        creating decrypted string from NoncePrivEncrypted
        """
        padding = M2Crypto.RSA.pkcs1_padding
        if not RsaPubKey:
            UsedRsaPubKey = self.ServerObj['RsaPubKey']
        else:
            UsedRsaPubKey = RsaPubKey
        try:
            NonceDecrypted = UsedRsaPubKey.public_decrypt ( NoncePrivEncrypted, padding )
        except:
            raise AuthError('decrypting of public key failed - abort!')
        return NonceDecrypted

    def NonceDecryptPrivate ( self, NoncePubEncrypted, RsaPKey=None ):
        padding = M2Crypto.RSA.pkcs1_padding
        if not RsaPKey:
            UsedRsaPKey = self.ServerObj['RsaPKey']
        else:
            UsedRsaPKey = RsaPKey
        NonceDecrypted = UsedRsaPKey.private_decrypt ( NoncePubEncrypted, padding )
        return NonceDecrypted

    def NonceVerify ( self, DecryptedNonce=None ):
        if  self.CurrentObj['Nonce']['Decrypted'] == DecryptNonce:
            return True
        return False

    #--------------------------------
    # CertHandler  authentication request
    #--------------------------------
    def ClientInit ( self, ObjName=None ):
        """
        generating AuthString 
            Nonce     messagedigest 'sha1', encrypted with own instance private key
            Cert      own instance X509 cert, PEM encoded
            any linefeed charaters stripped out of the base64 code
        return generated Nonce and AuthString
        """
        if ObjName:
            if self.PemMap.has_key( ObjName ):
                UsedObjName = ObjName
            else:
                UsedObjName = self.ServerName
        else:
            UsedObjName = self.ServerName

        NonceDecrypted     = self.CreateNonce ()
        NoncePrivEncrypted = re.sub('\012', '', base64.encodestring( self.NonceEncryptPrivate ( NonceDecrypted, RsaPKey=self.ServerObj['RsaPKey'] )) )
        PemCert            = re.sub('\012', '', base64.encodestring( self.KeyEnv['X509Cert'][0] + '\n' + string.join( self.PemMap[UsedObjName]['X509Cert'], '\n' ) + '\n' + self.KeyEnv['X509Cert'][1] + '\n' ))
        InitString         = re.sub('\012', '', base64.encodestring('%s:%s' % ( NoncePrivEncrypted, PemCert )))
        return ( NonceDecrypted, InitString )


    def ClientInitVerify ( self, InitString ):
        """
        return decrypted Nonce from AuthString and ObjName from AuthString X509 Cert
        """
        try:
            PemBaseString = base64.decodestring( InitString )
        except base64.binascii.Error, msg:
            raise base64.binascii.Error( msg )
        try:
            ( Base64Nonce, Base64Cert ) = re.split(':', PemBaseString )
        except:
            raise AuthError( 'cannot split PemBaseString into parts - abort!' )
        try:
            NoncePrivEncrypted = base64.decodestring( Base64Nonce )
        except base64.binascii.Error, msg:
            raise base64.binascii.Error( msg )
        try:
            PemCert = base64.decodestring( Base64Cert )
        except base64.binascii.Error, msg:
            raise base64.binascii.Error( msg )
        try:
            X509Cert = M2Crypto.X509.load_cert_string( PemCert )
        except:
            raise AuthError( 'cannot extract X509 cert from PEM representation - abort!' )
        EvpPKey = self.ObjMap['CA']['EvpPKey']
        if dir(EvpPKey).count('_ptr'):
            Result = X509Cert.verify ( EvpPKey._ptr() )
        else:
            Result = X509Cert.verify ( EvpPKey )
        if Result != 1:
            raise AuthError( 'verification of X509 cert with Certification Authority "CA" failed with code %d - abort!' % ( Result ))
        ClientObjName = self.ObjNameFromPemCert( PemCert=PemCert )
        try:
            NonceDecrypted = self.NonceDecryptPublic( NoncePrivEncrypted, RsaPubKey=self.CurrentObj['RsaPubKey'] )
        except:
            raise AuthError( 'wrong public key for encoding nonce - abort!' )

        return ( NonceDecrypted, ClientObjName )




    def ServerInit ( self, ClientObjName, ClientNonce ):
        """
        NonceServer       new Nonce from server encrypted with client publickey and base64 encoded
        NonceBounce       the authrequest nonce encrypted with server privatekey and base64 encoded
        PemServerCert     server X509 certification PEM encoded and base64 encoded
        """
        if not self.ObjMap.has_key( ClientObjName ):
            if not self.PemMap.has_key( ClientObjName ):
                raise AuthError( 'cannot find ClientObjName - abort!' )
            else:
                self.ObjFromContainer( ObjName=ClientObjName )
        else:
            self.CurrentObj = self.ObjMap[ClientObjName]

        NonceDecrypted  = self.CreateNonce ()
        NonceServer     = re.sub('\012', '', base64.encodestring( self.NonceEncryptPublic ( NonceDecrypted, RsaPubKey=self.CurrentObj['RsaPubKey'] )) )
        NonceBounce     = re.sub('\012', '', base64.encodestring( self.NonceEncryptPublic ( ClientNonce, RsaPubKey=self.CurrentObj['RsaPubKey'] )) )
        PemServerCert   = re.sub('\012', '', base64.encodestring( self.KeyEnv['X509Cert'][0] + '\n' + string.join( self.PemMap[self.ServerName]['X509Cert'], '\n' ) + '\n' + self.KeyEnv['X509Cert'][1] + '\n' ) )

        InitString      = re.sub('\012', '', base64.encodestring('%s:%s:%s' % ( NonceServer, NonceBounce, PemServerCert )) )
        return ( NonceDecrypted, InitString )


    def ServerInitVerify ( self, InitString, ObjName=None ):
        NonceDecrypted = ''
        ObjName        = ''
        try:
            PemBaseString = base64.decodestring( InitString )
        except:
            return False

        ( NonceServer, NonceBounce, ServerCert ) = re.split(':', PemBaseString )        
        NoncePubServer     = base64.decodestring( NonceServer )             # NonceServer
        NoncePubBounce     = base64.decodestring( NonceBounce )             # NonceBounce
        PemServerCert      = base64.decodestring( ServerCert  )             # PemServerCert

        try:
            X509Cert = M2Crypto.X509.load_cert_string( PemServerCert )
        except:
            return False

        # verify X509 cert 
        EvpPKey = self.ObjMap['CA']['EvpPKey']
        if dir(EvpPKey).count('_ptr'):
            Result = X509Cert.verify ( EvpPKey._ptr() )
        else:
            Result = X509Cert.verify ( EvpPKey )
        if not Result:
            return False

        # verify Nonce from Server encrypted with my own publickey
        try:
            NonceDecrypted = self.NonceDecryptPrivate( NoncePubServer, RsaPKey=self.ServerObj['RsaPKey']  )
        except:
            return False

        ServerObjName = self.ObjNameFromPemCert( PemCert=PemServerCert )

        # verify Nonce bounced from Server encrypted with server privatekey
        try:
            NonceBounceDecrypted = self.NonceDecryptPrivate( NoncePubBounce, RsaPKey=self.CurrentObj['RsaPKey'] )
        except:
            return False

        return ( NonceDecrypted, NonceBounceDecrypted, ServerObjName )



    def ReplyInit ( self, ReplyObjName, ReplyBounce ): 
        NonceDecrypted     = self.CreateNonce ()
        NoncePubInit       = re.sub('\012', '', base64.encodestring( self.NonceEncryptPublic ( NonceDecrypted, RsaPubKey=self.ObjMap[ ReplyObjName ]['RsaPubKey'] )) )
        NoncePubBounce     = re.sub('\012', '', base64.encodestring( self.NonceEncryptPublic ( ReplyBounce,    RsaPubKey=self.ObjMap[ ReplyObjName ]['RsaPubKey'] )) )
        ReplyString        = re.sub('\012', '', base64.encodestring('%s:%s' % ( NoncePubInit, NoncePubBounce )) )
        return ( NonceDecrypted, ReplyString )


    def ReplyVerify ( self, ReplyString ):
        try:
            PemBaseString = base64.decodestring( ReplyString )
        except base64.binascii.Error, msg:
            raise base64.binascii.Error( msg )
        ( NoncePubInit, NoncePubBounce ) = re.split(':', PemBaseString )

        try:
            NoncePubInit = base64.decodestring( NoncePubInit )      # new Nonce from Remote, encrypted with own publickey
        except base64.binascii.Error, msg:
            raise base64.binascii.Error( msg )
        try:
            NoncePubBounce = base64.decodestring( NoncePubBounce )      # bounced Nonce from Remote, encrypted with Remote privatekey
        except base64.binascii.Error, msg:
            raise base64.binascii.Error( msg )

        # verify Nonce from Remote encrypted with my own publickey
        try:
            NonceRemote = self.NonceDecryptPrivate( NoncePubInit, RsaPKey=self.ServerObj['RsaPKey'] )
        except:
            raise AuthError( 'cannot encode nonce with own private key - abort!' )

        # verify Nonce bounced from Remote encrypted with Remote privatekey
        try:
            NonceBounced = self.NonceDecryptPrivate( NoncePubBounce, RsaPKey=self.ServerObj['RsaPKey'] )
        except:
            raise AuthError( 'wrong public key for encoding nonce - abort!' )

        return ( NonceRemote, NonceBounced )




    #-------------------------------------------------------------------------------------------
    # TEST 
    #-------------------------------------------------------------------------------------------
    def CreateCAForContainer ( self ):
        self.CreateCert ()

    def CreateForContainer ( self, ObjName ):
        """
        create new pkey pair  and  x509 cert for specified objname
        result will be written in file "PyReprPem.txt"
        """
        self.ObjFromContainer ( ObjName='AuthInstance' )
        self.CreateObjCert ( ObjName=ObjName )


    def Test ( self ):
        #self.CreateCert ()
        #self.ExtractPublicKeyFromCert ()
        #self.VerifyCert ()

        ( ClientInitNonce, ClientInitString ) = self.ClientInit ()
        ( ClientSendNonce, ClientObjName )    = self.ClientInitVerify ( InitString=ClientInitString )
        ( ServerInitNonce, ServerInitString ) = self.ServerInit ( ClientObjName=ClientObjName, ClientNonce=ClientSendNonce )
        ( ServerSendNonce, ClientBounceNonce, ServerObjName )    = self.ServerInitVerify ( InitString=ServerInitString )
        if ClientInitNonce == ClientBounceNonce :
            print '100 Test  Nonce bounced True'
        else:
            print '100 Test  Nonce bounced False - abort!'

        ( ReplyInitNonce, ReplyInitString )   = self.ReplyInit ( ReplyObjName=ClientObjName, ReplyBounce=ServerSendNonce )
        ( ReplySendNonce, NonceBounced )      = self.ReplyVerify ( ReplyString=ReplyInitString )
        if ServerInitNonce == NonceBounced :
            print '100 Test  Nonce bounced True'
        else:
            print '100 Test  Nonce bounced False - abort!'

        ( Reply2InitNonce, Reply2InitString )   = self.ReplyInit ( ReplyObjName=ClientObjName, ReplyBounce=ServerSendNonce )
        ( Reply2SendNonce, Nonce2Bounced )      = self.ReplyVerify ( ReplyString=Reply2InitString )
        if ServerInitNonce == Nonce2Bounced :
            print '100 Test  Nonce bounced True'
        else:
            print '100 Test  Nonce bounced False - abort!'

        #self.NonceEncryptPrivate ()
        #self.NonceDecryptPublic ()
        #self.NonceVerify ()


#-----------------------------------------------------------------------------------------------
# MAIN
#
# x509auth.py --ca              
# will create a file "PyReprPem.txt" in the current directory
# append the contents of the file to the CertContainer in this script
#
# x509auth.py --cert <ObjName>  
# creates a file "PyReprPem.txt" in the current directory
# append the contents of the file to the CertContainer in this script
#
# x509auth.py --test            
# running authentification tests with bounced nonce
#
#-----------------------------------------------------------------------------------------------
if __name__ == '__main__':
    run = CertHandler ()

    if len( sys.argv ) > 1:
        if sys.argv[1] == '--test':
            run.Test ()
        elif sys.argv[1] == '--ca':
            run.CreateCert()
        elif sys.argv[1] == '--cert':
            run.CreateForContainer( sys.argv[2] )

    sys.exit( 0 )

