import sys, os, tempfile
import UserDict
from email import Message
import M2Crypto

if not (sys.version_info[0] >= 2 and sys.version_info[1] >= 2):
    class object:
        pass
    True=1
    False=0


class smimeplus(object):
    def __init__(self, cert, privkey, passphrase, cacert, randfile=None):
        self.cipher = 'des_ede3_cbc'   # XXX make it configable??
        self.setsender(cert, privkey, passphrase)
        self.setcacert(cacert)
        self.randfile = randfile
        self.__loadrand()
        
    def __passcallback(self, v):
        """private key passphrase callback function"""
        return self.passphrase

    def __loadrand(self):
        """Load random number file"""
        if self.randfile:
            M2Crypto.Rand.load_file(self.randfile, -1)

    def __saverand(self):
        """Save random number file"""
        if self.randfile:
            M2Crypto.Rand.save_file(self.randfile)

    def __gettext(self, msg):
        """Return a string representation of 'msg'"""
        _data = ''
        if isinstance(msg, Message.Message):
            for _p in msg.walk():
                _data = _data + _p.as_string()
        else:
            _data = str(msg)
        return _data

    def __pack(self, msg):
        """Convert 'msg' to string and put it into an memory buffer for 
           openssl operation"""
        return M2Crypto.BIO.MemoryBuffer(self.__gettext(msg))

    def setsender(self, cert=None, privkey=None, passphrase=None):
        if cert:
            self.cert = cert
        if privkey:
            self.key  = privkey
        if passphrase:
            self.passphrase  = passphrase

    def setcacert(self, cacert):
        self.cacert = cacert

    def sign(self, msg):
        """Sign a message"""
        _sender = M2Crypto.SMIME.SMIME()
        _sender.load_key_bio(self.__pack(self.key), self.__pack(self.cert),
                callback=self.__passcallback)

        _signed = _sender.sign(self.__pack(msg))

        _out = self.__pack(None)
        _sender.write(_out, _signed, self.__pack(msg))
        return _out.read()

    def verify(self, smsg, scert):
        """Verify to see if 'smsg' was signed by 'scert', and scert was
           issued by cacert of this object.  Return message signed if success, 
           None otherwise"""
        # Load signer's cert.
        _x509 = M2Crypto.X509.load_cert_bio(self.__pack(scert))
        _stack = M2Crypto.X509.X509_Stack()
        _stack.push(_x509)

        # Load CA cert.
        _tmpfile = persistdata(self.cacert)
        _store = M2Crypto.X509.X509_Store()
        _store.load_info(_tmpfile)
        os.remove(_tmpfile)

        # prepare SMIME object
        _sender = M2Crypto.SMIME.SMIME()
        _sender.set_x509_stack(_stack)
        _sender.set_x509_store(_store)
    
        # Load signed message, verify it, and return result
        _p7, _data = M2Crypto.SMIME.smime_load_pkcs7_bio(self.__pack(smsg))
        try:
            return _sender.verify(_p7, flags=M2Crypto.SMIME.PKCS7_SIGNED)
        except M2Crypto.SMIME.SMIME_Error, _msg:
            return None

    def encrypt(self, rcert, msg):
        # Instantiate an SMIME object.
        _sender = M2Crypto.SMIME.SMIME()
    
        # Load target cert to encrypt to.
        _x509 = M2Crypto.X509.load_cert_bio(self.__pack(rcert))
        _stack = M2Crypto.X509.X509_Stack()
        _stack.push(_x509)
        _sender.set_x509_stack(_stack)
    
        _sender.set_cipher(M2Crypto.SMIME.Cipher(self.cipher))
    
        # Encrypt the buffer.
        _buf = self.__pack(self.__gettext(msg))
        _p7 = _sender.encrypt(_buf)
        
        # Output p7 in mail-friendly format.
        _out = self.__pack('')
        _sender.write(_out, _p7)
    
        # Save the PRNG's state.
        self.__saverand()

        return _out.read()

    def decrypt(self, emsg):
        """decrypt 'msg'.  Return decrypt message if success, None
           otherwise"""
        # Load private key and cert.
        _sender = M2Crypto.SMIME.SMIME()
        _sender.load_key_bio(self.__pack(self.key), self.__pack(self.cert),
                callback=self.__passcallback)
    
        # Load the encrypted data.
        _p7, _data = M2Crypto.SMIME.smime_load_pkcs7_bio(self.__pack(emsg))
    
        # Decrypt p7.
        try:
            return _sender.decrypt(_p7)
        except M2Crypto.SMIME.SMIME_Error, _msg:
            return None

    def addHeader(self, rcert, content, subject=''):
        """Add To, From, Subject Header to 'content'"""
        _scert = M2Crypto.X509.load_cert_bio(self.__pack(self.cert))
        _scertsubj = X509_Subject(str(_scert.get_subject()))
        _rcert = M2Crypto.X509.load_cert_bio(self.__pack(rcert))
        _rcertsubj = X509_Subject(str(_rcert.get_subject()))

        _out = 'From: "%(CN)s" <%(emailAddress)s>\n' % _scertsubj
        _out = _out + 'To: "%(CN)s" <%(emailAddress)s>\n' % _rcertsubj
        _out = _out + 'Subject: %s\n' % subject
        _out = _out + content

        return _out


class X509_Subject(UserDict.UserDict):
    # This class needed to be rewritten or merge with X509_Name
    def __init__(self, substr):
        UserDict.UserDict.__init__(self)
        try:
            _data = substr.strip().split('/')
        except AttributeError, _msg:
            pass
        else:
            for _i in _data:
                try:
                    _k, _v = _i.split('=')
                    self[_k] = _v
                except ValueError, _msg:
                    pass


def persistdata(data, file=None, isbinary=False):
    if not file:
        file = tempfile.mktemp()
    if isbinary:
        _flag = 'wb'
    else:
        _flag = 'w'

    _fh = open(file, _flag)
    _fh.write(data)
    _fh.close()
    return file


