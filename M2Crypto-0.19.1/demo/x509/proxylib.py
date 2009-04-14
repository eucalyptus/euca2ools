############################################################################
# Matt Rodriguez, LBNL
#Copyright (c) 2003, The Regents of the University of California,
#through Lawrence Berkeley National Laboratory
#(subject to receipt of any required approvals from the U.S. Dept. of Energy).
#All rights reserved.
############################################################################
"""
API to generated proxy certificates
""" 
import os, sys 
import struct
import re
import time, calendar, datetime

import_regex = re.compile(r"\s*libssl.so.0.9.8\s*")
errstr = "You must have the openssl 0.9.8 libraries in your LD_LIBRARY_PATH"""

try:
    from M2Crypto import BIO, X509, RSA, EVP, ASN1
except ImportError, ex: 
    if import_regex.match(str(ex)):
        print errstr 
        sys.exit(-1)
    else:
        raise ex 

MBSTRING_FLAG = 0x1000
MBSTRING_ASC  = MBSTRING_FLAG | 1
KEY_USAGE_VALUE = "Digital Signature, Key Encipherment, Data Encipherment"
PCI_VALUE_FULL = "critical, language:Inherit all"
PCI_VALUE_LIMITED = "critical, language:1.3.6.1.4.1.3536.1.1.1.9"

def create_write_file(fname, perm=0600):
    """
    Creates a file to write to while avoiding a possible race condition.
    This is essential for writing out the proxy file. Need to make sure
    there is no pre-existing file.
    """
    if os.path.exists(fname):
        os.remove(fname)
    # Make sure the file doesn't exist. Will throw an exception if
    # it does. This would only happen if the code is attacked.
    fd = os.open(fname, os.O_CREAT|os.O_EXCL|os.O_WRONLY, perm)
    f = os.fdopen(fd, 'w')
    return f


class ProxyFactoryException(Exception):
    """
    Base class for exceptions in the ProxyFactory class
    """

class Proxy:
    """
    class that holds proxy certificate information,
    consisting of an issuer cert a user cert and 
    a key for the user cert
    """
    def __init__(self):
        self._key = None
        self._cert = None 
        self._issuer = None

    def read(self, proxypath=None):
        """
        reads in a proxy certificate information
        """
        if proxypath is None:
            proxypath = get_proxy_filename()
            
        proxyfile = open(proxypath)
        bio = BIO.File(proxyfile)    
        self._cert = X509.load_cert_bio(bio)
        self._key = RSA.load_key_bio(bio)
        self._issuer = X509.load_cert_bio(bio)
    
    def getcert(self):
        """
        Returns a X509 instance 
        """
        return self._cert

    def getkey(self):
        """
        Returns a RSA instance
        """
        return self._key

    def getissuer(self):
        """
        Returns a X509 instance 
        """ 
        return self._issuer

    def setcert(self, cert):
        """
        Sets the user cert should be a X509 instance
        """
        self._cert = cert

    def setkey(self, key):
        """
        Sets the user key should be a RSA instance
        """
        self._key = key 

    def setissuer(self, issuer):
        """
        Sets the issuer cert should be a X509 instance
        """
        self._issuer = issuer

    def write(self, proxypath=None):
        """
        Writes the proxy information to a file
        """
        proxyfile = create_write_file(proxypath)
        bio = BIO.File(proxyfile) 
        bio.write(self._cert.as_pem())
        self._key.save_key_bio(bio, cipher=None) 
        bio.write(self._issuer.as_pem())
        bio.close()
        os.chmod(proxypath, 0600) 
        

class ProxyFactory:
    """
    Creates proxies
    """
    def __init__(self, kw={'cert':None,'key':None,'valid':(12,0),'full':True}):
        
        self._usercert = get_usercert(kw['cert']) 
        self._userkey = get_userkey(kw['key']) 
        self._proxycert = None
        self._proxykey = None 
        self._valid = kw['valid'] 
        self._full = kw['full']
        
    def generate(self): 
        """
        generates a new proxy like grid-proxy-init 
        """ 
        if not self._check_valid():
            raise ProxyFactoryException("The issuer cert is expired")
        if self._proxycert is None:
            self._proxycert = X509.X509()        
            key = EVP.PKey()
            self._proxykey = RSA.gen_key(512, 65537)
            key.assign_rsa(self._proxykey, capture=0)
            self._proxycert.set_pubkey(key)
        self._proxycert.set_version(2)
        self._set_times()
        issuer_name = self._usercert.get_subject()
        self._proxycert.set_issuer_name(issuer_name) 
        serial_number = self._make_serial_number(self._proxycert) 
        self._proxycert.set_serial_number(serial_number)
        self._set_subject()
        sign_pk = EVP.PKey()
        sign_pk.assign_rsa(self._userkey) 
        self._add_extensions() 
        self._proxycert.sign(sign_pk, 'md5')  

    def set_proxycert(self, proxycert):
        """
        This method is useful if you don't
        want to pay the costs associated with
        generating a new key pair.
        """
        self._proxycert = proxycert 

    def getproxy(self): 
        """
        Return a proxy instance
        """
        proxy = Proxy() 
        proxy.setissuer(self._usercert)
        proxy.setcert(self._proxycert)
        proxy.setkey(self._proxykey)
        return proxy
    
    def _set_subject(self):
        """
        Internal method that sets the subject name
        """
        subject_name = X509.X509_Name() 
        serial_number = self._make_serial_number(self._proxycert) 
        issuer_name = self._usercert.get_subject()
        issuer_name_txt = issuer_name.as_text() 
        seq = issuer_name_txt.split(",")
        for entry in seq:
            name_component = entry.split("=") 
            subject_name.add_entry_by_txt(field=name_component[0].strip(),
                                         type=MBSTRING_ASC,
                                         entry=name_component[1],len=-1,
                                         loc=-1, set=0)
        
        
        subject_name.add_entry_by_txt(field="CN", 
                                      type=MBSTRING_ASC, 
                                      entry=str(serial_number), 
                                      len=-1, loc=-1, set=0)
        
        self._proxycert.set_subject_name(subject_name)
    
    def _set_times(self):
        """
        Internal function that sets the time on the proxy
        certificate
        """
        not_before = ASN1.ASN1_UTCTIME()
        not_after = ASN1.ASN1_UTCTIME()
        not_before.set_time(int(time.time())) 
        offset = (self._valid[0] * 3600) + (self._valid[1] * 60)
        not_after.set_time(int(time.time()) + offset )
        self._proxycert.set_not_before(not_before)
        self._proxycert.set_not_after(not_after)

    def _make_serial_number(self, cert):
        """
        Lifted from the globus code
        """
        message_digest = EVP.MessageDigest('sha1')
        pubkey = cert.get_pubkey()
        der_encoding = pubkey.as_der() 
        message_digest.update(der_encoding)
        digest = message_digest.final()
        digest_tuple = struct.unpack('BBBB', digest[:4])
        sub_hash = long(digest_tuple[0] + (digest_tuple[1] + ( digest_tuple[2] + 
                       ( digest_tuple[3] >> 1) * 256 ) * 256) * 256) 
        return sub_hash
    
    def _add_extensions(self):
        """
        Internal method that adds the extensions to the certificate
        """
        key_usage_ext = X509.new_extension("keyUsage", KEY_USAGE_VALUE, 1) 
        self._proxycert.add_ext(key_usage_ext)
        if self._full:
            pci_ext = X509.new_extension("proxyCertInfo", 
                                        PCI_VALUE_FULL, 1, 0)  
        else:
            pci_ext = X509.new_extension("proxyCertInfo", 
                                        PCI_VALUE_LIMITED, 1, 0)  
        self._proxycert.add_ext(pci_ext)
 
    def _check_valid(self):
        """
        Internal method that ensures the issuer cert has
        valid, not_before and not_after fields
        """
        before_time = self._usercert.get_not_before()
        after_time = self._usercert.get_not_after()
        before_tuple = time.strptime(str(before_time), "%b %d %H:%M:%S %Y %Z")
        after_tuple = time.strptime(str(after_time), "%b %d %H:%M:%S %Y %Z")
        starts =  datetime.timedelta(seconds=calendar.timegm(before_tuple))
        expires = datetime.timedelta(seconds=calendar.timegm(after_tuple))
        now = datetime.timedelta(seconds=time.time())
        time_delta = expires - now
        #cert has expired
        if time_delta.days < 0:
            return False
        #cert is not yet valid, not likely but should still return False
        time_delta = now - starts
        if time_delta.days < 0:   
            return False
        
        return True
    
#Utility Functions
def get_proxy_filename():  
    """
    function that returns the default proxy path 
    which is /tmp/x509up_uuid
    """
    if os.name == 'posix':
        proxy_filename = "x509up_u" + (str(os.getuid())) 
        proxypath = os.path.join("/tmp", proxy_filename) 
    elif os.name == 'nt':
        username = os.getenv("USERNAME")
        if username is None:
            raise RuntimeError("""USERNAME is not set in environment. Can't 
            determine proxy file location""")
             
        proxy_filename = "x509up_u" + username
        drive = os.path.splitdrive(os.getcwd())[0]
        proxydir = drive + os.sep + "temp"
        proxypath = os.path.join(proxydir, proxy_filename) 
    else:
        except_string = """get_proxy_filename is not supported on this platform
                           Try explicitly specifying the location of the 
                           proxyfile""" 
        raise RuntimeError(except_string)
    return proxypath

def get_usercert(certfile=None):
    """
    function that returns a X509 instance which 
    is the user cert that is expected to be a ~/.globus/usercert.pem
    
    A check is performed to ensure the certificate has valid
    before and after times.
    """
    if certfile is None:
        certfile = open(os.path.join(os.getenv("HOME"),
                                    ".globus","usercert.pem"))
    else:
        certfile = open(certfile)
    bio = BIO.File(certfile)
    cert = X509.load_cert_bio(bio) 
    return cert

def get_userkey(keyfile=None):
    """
    function that returns a X509 instance which 
    is the user cert that is expected to be a ~/.globus/userkey.pem
    """
    if keyfile is None:
        keyfile = open(os.path.join(os.getenv("HOME"),
                                   ".globus","userkey.pem")) 
    else:
        keyfile = open(keyfile)
    bio = BIO.File(keyfile)
    key = RSA.load_key_bio(bio)
    return key


