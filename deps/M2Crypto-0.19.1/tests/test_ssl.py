#!/usr/bin/env python

"""Unit tests for M2Crypto.SSL.

Copyright (c) 2000-2004 Ng Pheng Siong. All rights reserved."""

"""
TODO

Server tests:
- ???

Others:
- ssl_dispatcher
- SSLServer
- ForkingSSLServer
- ThreadingSSLServer
"""

import os, socket, string, sys, tempfile, thread, time, unittest
from M2Crypto import Rand, SSL, m2, Err

srv_host = 'localhost'
srv_port = 64000

def verify_cb_new_function(ok, store):
    try:
        assert not ok
        err = store.get_error()
        assert err in [m2.X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT,
                       m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY,
                       m2.X509_V_ERR_CERT_UNTRUSTED,
                       m2.X509_V_ERR_UNABLE_TO_VERIFY_LEAF_SIGNATURE]
        app_data = m2.x509_store_ctx_get_app_data(store.ctx)
        assert app_data
        x509 = store.get_current_cert()
        assert x509
        stack = store.get1_chain()
        assert len(stack) == 1
        assert stack[0].as_pem() == x509.as_pem()
    except AssertionError, e:
        # If we let exceptions propagate from here the
        # caller may see strange errors. This is cleaner.
        return 0   
    return 1

class VerifyCB:
    def __call__(self, ok, store):
        return verify_cb_new_function(ok, store)

sleepTime = float(os.getenv('M2CRYPTO_TEST_SSL_SLEEP', 0.5))

class BaseSSLClientTestCase(unittest.TestCase):

    def start_server(self, args):
        pid = os.fork()
        if pid == 0:
            # openssl must be started in the tests directory for it
            # to find the .pem files
            os.chdir('tests')
            try:
                os.execvp('openssl', args)
            finally:
                os.chdir('..')
                
        else:
            time.sleep(sleepTime)
            return pid

    def stop_server(self, pid):
        os.kill(pid, 1)
        os.waitpid(pid, 0)

    def http_get(self, s):
        s.send('GET / HTTP/1.0\n\n') 
        resp = ''
        while 1:
            try:
                r = s.recv(4096)
                if not r:
                    break
            except SSL.SSLError: # s_server throws an 'unexpected eof'...
                break
            resp = resp + r 
        return resp

    def setUp(self):
        self.srv_host = srv_host
        self.srv_port = srv_port
        self.srv_addr = (srv_host, srv_port)
        self.srv_url = 'https://%s:%s/' % (srv_host, srv_port)
        self.args = ['s_server', '-quiet', '-www',
                     #'-cert', 'server.pem', Implicitly using this
                     '-accept', str(self.srv_port)]

    def tearDown(self):
        global srv_port
        srv_port = srv_port - 1


class PassSSLClientTestCase(BaseSSLClientTestCase):
        
    def test_pass(self):
        pass

class HttpslibSSLClientTestCase(BaseSSLClientTestCase):

    def test_HTTPSConnection(self):
        pid = self.start_server(self.args)
        try:
            from M2Crypto import httpslib
            c = httpslib.HTTPSConnection(srv_host, srv_port)
            c.request('GET', '/')
            data = c.getresponse().read()
            c.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_HTTPSConnection_resume_session(self):
        pid = self.start_server(self.args)
        try:
            from M2Crypto import httpslib
            ctx = SSL.Context()
            ctx.load_verify_locations(cafile='tests/ca.pem')
            ctx.load_cert('tests/x509.pem')
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 1)
            ctx.set_session_cache_mode(m2.SSL_SESS_CACHE_CLIENT)
            c = httpslib.HTTPSConnection(srv_host, srv_port, ssl_context=ctx)
            c.request('GET', '/')
            ses = c.get_session()
            t = ses.as_text()
            data = c.getresponse().read()
            c.close()
            
            ctx2 = SSL.Context()
            ctx2.load_verify_locations(cafile='tests/ca.pem')
            ctx2.load_cert('tests/x509.pem')
            ctx2.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 1)
            ctx2.set_session_cache_mode(m2.SSL_SESS_CACHE_CLIENT)
            c = httpslib.HTTPSConnection(srv_host, srv_port, ssl_context=ctx2)
            c.set_session(ses)
            c.request('GET', '/')
            ses2 = c.get_session()
            t2 = ses2.as_text()
            data = c.getresponse().read()
            c.close()
            assert t == t2, "Sessions did not match"
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_HTTPSConnection_secure_context(self):
        pid = self.start_server(self.args)
        try:
            from M2Crypto import httpslib
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/ca.pem')
            c = httpslib.HTTPSConnection(srv_host, srv_port, ssl_context=ctx)
            c.request('GET', '/')
            data = c.getresponse().read()
            c.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_HTTPSConnection_secure_context_fail(self):
        pid = self.start_server(self.args)
        try:
            from M2Crypto import httpslib
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/server.pem')
            c = httpslib.HTTPSConnection(srv_host, srv_port, ssl_context=ctx)
            self.assertRaises(SSL.SSLError, c.request, 'GET', '/')
            c.close()
        finally:
            self.stop_server(pid)

    def test_HTTPS(self):
        pid = self.start_server(self.args)
        try:
            from M2Crypto import httpslib
            c = httpslib.HTTPS(srv_host, srv_port)
            c.putrequest('GET', '/')
            c.putheader('Accept', 'text/html')
            c.putheader('Accept', 'text/plain')
            c.endheaders()
            err, msg, headers = c.getreply()
            assert err == 200, err
            f = c.getfile()
            data = f.read()
            c.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_HTTPS_secure_context(self):
        pid = self.start_server(self.args)
        try:
            from M2Crypto import httpslib
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/ca.pem')
            c = httpslib.HTTPS(srv_host, srv_port, ssl_context=ctx)
            c.putrequest('GET', '/')
            c.putheader('Accept', 'text/html')
            c.putheader('Accept', 'text/plain')
            c.endheaders()
            err, msg, headers = c.getreply()
            assert err == 200, err
            f = c.getfile()
            data = f.read()
            c.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_HTTPS_secure_context_fail(self):
        pid = self.start_server(self.args)
        try:
            from M2Crypto import httpslib
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/server.pem')
            c = httpslib.HTTPS(srv_host, srv_port, ssl_context=ctx)
            c.putrequest('GET', '/')
            c.putheader('Accept', 'text/html')
            c.putheader('Accept', 'text/plain')
            self.assertRaises(SSL.SSLError, c.endheaders)
            c.close()
        finally:
            self.stop_server(pid)
            
    def test_HTTPSConnection_illegalkeywordarg(self):
        from M2Crypto import httpslib
        self.assertRaises(ValueError, httpslib.HTTPSConnection, 'example.org',
                          badKeyword=True)


class MiscSSLClientTestCase(BaseSSLClientTestCase):

    def test_no_connection(self):
        ctx = SSL.Context()
        s = SSL.Connection(ctx)
        
    def test_server_simple(self):
        pid = self.start_server(self.args)
        try:
            self.assertRaises(ValueError, SSL.Context, 'tlsv5')
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            s.connect(self.srv_addr)
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_server_simple_secure_context(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/ca.pem')
            s = SSL.Connection(ctx)
            s.connect(self.srv_addr)
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_server_simple_secure_context_fail(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/server.pem')
            s = SSL.Connection(ctx)
            self.assertRaises(SSL.SSLError, s.connect, self.srv_addr)
            s.close()
        finally:
            self.stop_server(pid)

    def test_server_simple_timeouts(self):
        pid = self.start_server(self.args)
        try:
            self.assertRaises(ValueError, SSL.Context, 'tlsv5')
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            
            r = s.get_socket_read_timeout()
            w = s.get_socket_write_timeout()
            assert r.sec == 0, r.sec
            assert r.microsec == 0, r.microsec
            assert w.sec == 0, w.sec
            assert w.microsec == 0, w.microsec

            s.set_socket_read_timeout(SSL.timeout())
            s.set_socket_write_timeout(SSL.timeout(909,9))
            r = s.get_socket_read_timeout()
            w = s.get_socket_write_timeout()
            assert r.sec == 600, r.sec
            assert r.microsec == 0, r.microsec
            assert w.sec == 909, w.sec
            #assert w.microsec == 9, w.microsec XXX 4000
            
            s.connect(self.srv_addr)
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_tls1_nok(self):
        self.args.append('-no_tls1')
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context('tlsv1')
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                self.failUnlessEqual(e[0], 'wrong version number')
            s.close()
        finally:
            self.stop_server(pid)

    def test_tls1_ok(self):
        self.args.append('-tls1')
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context('tlsv1')
            s = SSL.Connection(ctx)
            s.connect(self.srv_addr)
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_sslv23_no_v2(self):
        self.args.append('-no_tls1')
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context('sslv23')
            s = SSL.Connection(ctx)
            s.connect(self.srv_addr)
            self.failUnlessEqual(s.get_version(), 'SSLv3')
            s.close()
        finally:
            self.stop_server(pid)

    def test_sslv23_no_v2_no_service(self):
        self.args = self.args + ['-no_tls1', '-no_ssl3']
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context('sslv23')
            s = SSL.Connection(ctx)
            self.assertRaises(SSL.SSLError, s.connect, self.srv_addr)
            s.close()
        finally:
            self.stop_server(pid)

    def test_sslv23_weak_crypto(self):
        self.args = self.args + ['-no_tls1', '-no_ssl3']
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context('sslv23', weak_crypto=1)
            s = SSL.Connection(ctx)
            s.connect(self.srv_addr)
            self.failUnlessEqual(s.get_version(), 'SSLv2')
            s.close()
        finally:
            self.stop_server(pid)

    def test_cipher_mismatch(self):
        self.args = self.args + ['-cipher', 'EXP-RC4-MD5']
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            s.set_cipher_list('EXP-RC2-CBC-MD5')
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                self.failUnlessEqual(e[0], 'sslv3 alert handshake failure')
            s.close()
        finally:
            self.stop_server(pid)
        
    def test_no_such_cipher(self):
        self.args = self.args + ['-cipher', 'EXP-RC4-MD5']
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            s.set_cipher_list('EXP-RC2-MD5')
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                self.failUnlessEqual(e[0], 'no ciphers available')
            s.close()
        finally:
            self.stop_server(pid)
        
    def test_no_weak_cipher(self):
        self.args = self.args + ['-cipher', 'EXP']
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                self.failUnlessEqual(e[0], 'sslv3 alert handshake failure')
            s.close()
        finally:
            self.stop_server(pid)
        
    def test_use_weak_cipher(self):
        self.args = self.args + ['-cipher', 'EXP']
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context(weak_crypto=1)
            s = SSL.Connection(ctx)
            s.connect(self.srv_addr)
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)
        
    def test_cipher_ok(self):
        self.args = self.args + ['-cipher', 'EXP-RC4-MD5']
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            s.set_cipher_list('EXP-RC4-MD5')
            s.connect(self.srv_addr)
            data = self.http_get(s)
            
            assert s.get_cipher().name() == 'EXP-RC4-MD5', s.get_cipher().name()
            
            cipher_stack = s.get_ciphers()
            assert cipher_stack[0].name() == 'EXP-RC4-MD5', cipher_stack[0].name()
            self.assertRaises(IndexError, cipher_stack.__getitem__, 2)
            # For some reason there are 2 entries in the stack
            #assert len(cipher_stack) == 1, len(cipher_stack)
            assert s.get_cipher_list() == 'EXP-RC4-MD5', s.get_cipher_list()
            
            # Test Cipher_Stack iterator
            i = 0
            for cipher in cipher_stack:
                i += 1
                assert cipher.name() == 'EXP-RC4-MD5', '"%s"' % cipher.name()
            # For some reason there are 2 entries in the stack
            #assert i == 1, i
            
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)
        
    def verify_cb_new(self, ok, store):
        return verify_cb_new_function(ok, store)

    def test_verify_cb_new(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           self.verify_cb_new)
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_cb_new_class(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           VerifyCB())
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_cb_new_function(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           verify_cb_new_function)
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_cb_lambda(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           lambda ok, store: 1)
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def verify_cb_exception(self, ok, store):
        raise Exception, 'We should fail verification'

    def test_verify_cb_exception(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           self.verify_cb_exception)
            s = SSL.Connection(ctx)
            self.assertRaises(SSL.SSLError, s.connect, self.srv_addr)
            s.close()
        finally:
            self.stop_server(pid)

    def test_verify_cb_not_callable(self):
        ctx = SSL.Context()
        self.assertRaises(TypeError,
                          ctx.set_verify,
                          SSL.verify_peer | SSL.verify_fail_if_no_peer_cert,
                          9,
                          1)

    def test_verify_cb_wrong_callable(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           lambda _: '')
            s = SSL.Connection(ctx)
            self.assertRaises(SSL.SSLError, s.connect, self.srv_addr)
            s.close()
        finally:
            self.stop_server(pid)

    def verify_cb_old(self, ctx_ptr, x509_ptr, err, depth, ok):
        try:
            from M2Crypto import X509
            assert not ok
            assert err == m2.X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT or \
                   err == m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY or \
                   err == m2.X509_V_ERR_CERT_UNTRUSTED or \
                   err == m2.X509_V_ERR_UNABLE_TO_VERIFY_LEAF_SIGNATURE
            assert m2.ssl_ctx_get_cert_store(ctx_ptr)
            assert X509.X509(x509_ptr).as_pem()
        except AssertionError:
            # If we let exceptions propagate from here the
            # caller may see strange errors. This is cleaner.
            return 0
        return 1

    def test_verify_cb_old(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           self.verify_cb_old)
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_allow_unknown_old(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           SSL.cb.ssl_verify_callback)
            ctx.set_allow_unknown_ca(1)
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_allow_unknown_new(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9,
                           SSL.cb.ssl_verify_callback_allow_unknown_ca)
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_cert(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/ca.pem')
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_cert_fail(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/server.pem')
            s = SSL.Connection(ctx)
            self.assertRaises(SSL.SSLError, s.connect, self.srv_addr)
            s.close()
        finally:
            self.stop_server(pid)

    def test_verify_cert_mutual_auth(self):
        self.args.extend(['-Verify', '2', '-CAfile', 'ca.pem'])        
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/ca.pem')
            ctx.load_cert('tests/x509.pem')
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_cert_mutual_auth_servernbio(self):
        self.args.extend(['-Verify', '2', '-CAfile', 'ca.pem', '-nbio'])
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/ca.pem')
            ctx.load_cert('tests/x509.pem')
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_verify_cert_mutual_auth_fail(self):
        self.args.extend(['-Verify', '2', '-CAfile', 'ca.pem'])        
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/ca.pem')
            s = SSL.Connection(ctx)
            self.assertRaises(SSL.SSLError, s.connect, self.srv_addr)
            s.close()
        finally:
            self.stop_server(pid)

    def test_verify_nocert_fail(self):
        self.args.extend(['-nocert'])        
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
            ctx.load_verify_locations('tests/ca.pem')
            s = SSL.Connection(ctx)
            self.assertRaises(SSL.SSLError, s.connect, self.srv_addr)
            s.close()
        finally:
            self.stop_server(pid)

    def test_blocking0(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            s.setblocking(0)
            self.assertRaises(Exception, s.connect, self.srv_addr)
            s.close()
        finally:
            self.stop_server(pid)

    def test_blocking1(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            s.setblocking(1)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            data = self.http_get(s)
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_makefile(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            bio = s.makefile('rw')
            #s.close()  # XXX bug 6628?
            bio.write('GET / HTTP/1.0\n\n')
            bio.flush()
            data = bio.read()
            bio.close()
            s.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    def test_makefile_err(self):
        pid = self.start_server(self.args)
        try:
            ctx = SSL.Context()
            s = SSL.Connection(ctx)
            try:
                s.connect(self.srv_addr)
            except SSL.SSLError, e:
                assert 0, e
            f = s.makefile()
            data = self.http_get(s)
            s.close()
            del f
            del s
            err_code = Err.peek_error_code()
            assert not err_code, 'Unexpected error: %s' % err_code
            err = Err.get_error()
            assert not err, 'Unexpected error: %s' % err
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)


class UrllibSSLClientTestCase(BaseSSLClientTestCase):

    def test_urllib(self):
        pid = self.start_server(self.args)
        try:
            from M2Crypto import m2urllib
            url = m2urllib.FancyURLopener()
            url.addheader('Connection', 'close')
            u = url.open('https://%s:%s/' % (srv_host, srv_port))
            data = u.read()
            u.close()
        finally:
            self.stop_server(pid)
        self.failIf(string.find(data, 's_server -quiet -www') == -1)

    # XXX Don't actually know how to use m2urllib safely!
    #def test_urllib_secure_context(self):
    #def test_urllib_secure_context_fail(self):

    # XXX Don't actually know how to use m2urllib safely!
    #def test_urllib_safe_context(self):
    #def test_urllib_safe_context_fail(self):


class Urllib2SSLClientTestCase(BaseSSLClientTestCase):

    if sys.version_info >= (2,4):
        def test_urllib2(self):
            pid = self.start_server(self.args)
            try:
                from M2Crypto import m2urllib2
                opener = m2urllib2.build_opener()
                opener.addheaders = [('Connection', 'close')]
                u = opener.open('https://%s:%s/' % (srv_host, srv_port))
                data = u.read()
                u.close()
            finally:
                self.stop_server(pid)
            self.failIf(string.find(data, 's_server -quiet -www') == -1)
    
        def test_urllib2_secure_context(self):
            pid = self.start_server(self.args)
            try:
                ctx = SSL.Context()
                ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
                ctx.load_verify_locations('tests/ca.pem')
                
                from M2Crypto import m2urllib2
                opener = m2urllib2.build_opener(ctx)
                opener.addheaders = [('Connection', 'close')]           
                u = opener.open('https://%s:%s/' % (srv_host, srv_port))
                data = u.read()
                u.close()
            finally:
                self.stop_server(pid)
            self.failIf(string.find(data, 's_server -quiet -www') == -1)
    
        def test_urllib2_secure_context_fail(self):
            pid = self.start_server(self.args)
            try:
                ctx = SSL.Context()
                ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
                ctx.load_verify_locations('tests/server.pem')
                
                from M2Crypto import m2urllib2
                opener = m2urllib2.build_opener(ctx)
                opener.addheaders = [('Connection', 'close')]
                self.assertRaises(SSL.SSLError, opener.open, 'https://%s:%s/' % (srv_host, srv_port))
            finally:
                self.stop_server(pid)

        def test_z_urllib2_opener(self):
            pid = self.start_server(self.args)
            try:
                ctx = SSL.Context()

                from M2Crypto import m2urllib2
                opener = m2urllib2.build_opener(ctx, m2urllib2.HTTPBasicAuthHandler())
                m2urllib2.install_opener(opener)
                req = m2urllib2.Request('https://%s:%s/' % (srv_host, srv_port))
                u = m2urllib2.urlopen(req)
                data = u.read()
                u.close()
            finally:
                self.stop_server(pid)
            self.failIf(string.find(data, 's_server -quiet -www') == -1)

        def test_urllib2_opener_handlers(self):
            ctx = SSL.Context()

            from M2Crypto import m2urllib2
            opener = m2urllib2.build_opener(ctx,
                                            m2urllib2.HTTPBasicAuthHandler())


class TwistedSSLClientTestCase(BaseSSLClientTestCase):

    def test_twisted_wrapper(self):
        # Test only when twisted and ZopeInterfaces are present
        try:
            from twisted.internet.protocol import ClientFactory
            from twisted.protocols.basic import LineReceiver
            from twisted.internet import reactor
            import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
        except ImportError:
            import warnings
            warnings.warn('Skipping twisted wrapper test because twisted not found')
            return
        
        class EchoClient(LineReceiver):
            def connectionMade(self):
                self.sendLine('GET / HTTP/1.0\n\n')

            def lineReceived(self, line):
                global twisted_data
                twisted_data += line

        class EchoClientFactory(ClientFactory):
            protocol = EchoClient
        
            def clientConnectionFailed(self, connector, reason):
                reactor.stop()
                assert 0, reason
        
            def clientConnectionLost(self, connector, reason):
                reactor.stop()
                
        pid = self.start_server(self.args)

        class ContextFactory:
            def getContext(self):
                return SSL.Context()

        try:
            global twisted_data
            twisted_data = ''
            
            contextFactory = ContextFactory()
            factory = EchoClientFactory()
            wrapper.connectSSL(srv_host, srv_port, factory, contextFactory)
            reactor.run() # This will block until reactor.stop() is called
        finally:
            self.stop_server(pid)
        self.failIf(string.find(twisted_data, 's_server -quiet -www') == -1)


twisted_data = ''

class CheckerTestCase(unittest.TestCase):
    def test_checker(self):
        from M2Crypto.SSL import Checker
        from M2Crypto import X509

        check = Checker.Checker(host=srv_host,
                                peerCertHash='02C0CAD90DE6837700173A839BB8E84BF1F5B820')
        x509 = X509.load_cert('tests/server.pem')
        assert check(x509, srv_host)
        self.assertRaises(Checker.WrongHost, check, x509, 'example.com')
        
        import doctest
        doctest.testmod(Checker)
        
    
class ContextTestCase(unittest.TestCase):
    def test_ctx_load_verify_locations(self):
        ctx = SSL.Context()
        self.assertRaises(ValueError, ctx.load_verify_locations, None, None)
        
    def test_map(self):
        from M2Crypto.SSL.Context import map, _ctxmap
        assert isinstance(map(), _ctxmap)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CheckerTestCase))
    suite.addTest(unittest.makeSuite(ContextTestCase))
    suite.addTest(unittest.makeSuite(PassSSLClientTestCase))
    suite.addTest(unittest.makeSuite(HttpslibSSLClientTestCase))
    suite.addTest(unittest.makeSuite(UrllibSSLClientTestCase))
    suite.addTest(unittest.makeSuite(Urllib2SSLClientTestCase))
    suite.addTest(unittest.makeSuite(MiscSSLClientTestCase))
    suite.addTest(unittest.makeSuite(TwistedSSLClientTestCase))
    return suite    
    

def zap_servers():
    s = 's_server'
    fn = tempfile.mktemp() 
    cmd = 'ps | egrep %s > %s' % (s, fn)
    os.system(cmd)
    f = open(fn)
    while 1:
        ps = f.readline()
        if not ps:
            break
        chunk = string.split(ps)
        pid, cmd = chunk[0], chunk[4]
        if cmd == s:
            os.kill(int(pid), 1)
    f.close()
    os.unlink(fn)


if __name__ == '__main__':
    report_leaks = 0
    
    if report_leaks:
        import gc
        gc.enable()
        gc.set_debug(gc.DEBUG_LEAK & ~gc.DEBUG_SAVEALL)
    
    try:
        Rand.load_file('randpool.dat', -1) 
        unittest.TextTestRunner().run(suite())
        Rand.save_file('randpool.dat')
    finally:
        zap_servers()

    if report_leaks:
        import alltests
        alltests.dump_garbage()
