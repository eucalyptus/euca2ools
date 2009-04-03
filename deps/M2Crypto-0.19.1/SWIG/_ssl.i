/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/* Copyright (c) 1999-2004 Ng Pheng Siong. All rights reserved. */
/*
** Portions created by Open Source Applications Foundation (OSAF) are
** Copyright (C) 2004-2005 OSAF. All Rights Reserved.
*/
/* $Id: _ssl.i 616 2008-09-15 05:28:29Z heikki $ */

%{
#include <pythread.h>
#include <openssl/bio.h>
#include <openssl/dh.h>
#include <openssl/ssl.h>
#include <openssl/x509.h>
%}

%apply Pointer NONNULL { SSL_CTX * };
%apply Pointer NONNULL { SSL * };
%apply Pointer NONNULL { SSL_CIPHER * };
%apply Pointer NONNULL { STACK * };
%apply Pointer NONNULL { BIO * };
%apply Pointer NONNULL { DH * };
%apply Pointer NONNULL { RSA * };
%apply Pointer NONNULL { EVP_PKEY *};
%apply Pointer NONNULL { PyObject *pyfunc };

%rename(ssl_get_version) SSL_get_version;
extern const char *SSL_get_version(CONST SSL *);
%rename(ssl_get_error) SSL_get_error;
extern int SSL_get_error(CONST SSL *, int);
%rename(ssl_get_state) SSL_state_string;
extern const char *SSL_state_string(const SSL *);
%rename(ssl_get_state_v) SSL_state_string_long;
extern const char *SSL_state_string_long(const SSL *);
%rename(ssl_get_alert_type) SSL_alert_type_string;
extern const char *SSL_alert_type_string(int);
%rename(ssl_get_alert_type_v) SSL_alert_type_string_long;
extern const char *SSL_alert_type_string_long(int);
%rename(ssl_get_alert_desc) SSL_alert_desc_string;
extern const char *SSL_alert_desc_string(int);
%rename(ssl_get_alert_desc_v) SSL_alert_desc_string_long;
extern const char *SSL_alert_desc_string_long(int);

%rename(sslv2_method) SSLv2_method;
extern SSL_METHOD *SSLv2_method(void);
%rename(sslv3_method) SSLv3_method;
extern SSL_METHOD *SSLv3_method(void);
%rename(sslv23_method) SSLv23_method;
extern SSL_METHOD *SSLv23_method(void);
%rename(tlsv1_method) TLSv1_method;
extern SSL_METHOD *TLSv1_method(void);

%rename(ssl_ctx_new) SSL_CTX_new;
extern SSL_CTX *SSL_CTX_new(SSL_METHOD *);
%rename(ssl_ctx_free) SSL_CTX_free;
extern void SSL_CTX_free(SSL_CTX *);
%rename(ssl_ctx_set_verify_depth) SSL_CTX_set_verify_depth;
extern void SSL_CTX_set_verify_depth(SSL_CTX *, int);
%rename(ssl_ctx_get_verify_depth) SSL_CTX_get_verify_depth;
extern int SSL_CTX_get_verify_depth(CONST SSL_CTX *);
%rename(ssl_ctx_get_verify_mode) SSL_CTX_get_verify_mode;
extern int SSL_CTX_get_verify_mode(CONST SSL_CTX *);
%rename(ssl_ctx_set_cipher_list) SSL_CTX_set_cipher_list;
extern int SSL_CTX_set_cipher_list(SSL_CTX *, const char *);
%rename(ssl_ctx_add_session) SSL_CTX_add_session;
extern int SSL_CTX_add_session(SSL_CTX *, SSL_SESSION *);
%rename(ssl_ctx_remove_session) SSL_CTX_remove_session;
extern int SSL_CTX_remove_session(SSL_CTX *, SSL_SESSION *);
%rename(ssl_ctx_set_session_timeout) SSL_CTX_set_timeout;
extern long SSL_CTX_set_timeout(SSL_CTX *, long);
%rename(ssl_ctx_get_session_timeout) SSL_CTX_get_timeout;
extern long SSL_CTX_get_timeout(CONST SSL_CTX *);
%rename(ssl_ctx_get_cert_store) SSL_CTX_get_cert_store;
extern X509_STORE *SSL_CTX_get_cert_store(CONST SSL_CTX *);

%rename(bio_new_ssl) BIO_new_ssl;
extern BIO *BIO_new_ssl(SSL_CTX *, int);

%rename(ssl_new) SSL_new;
extern SSL *SSL_new(SSL_CTX *);
%rename(ssl_free) SSL_free;
extern void SSL_free(SSL *);
%rename(ssl_dup) SSL_dup;
extern SSL *SSL_dup(SSL *);
%rename(ssl_set_bio) SSL_set_bio;
extern void SSL_set_bio(SSL *, BIO *, BIO *);
%rename(ssl_set_accept_state) SSL_set_accept_state;
extern void SSL_set_accept_state(SSL *);
%rename(ssl_set_connect_state) SSL_set_connect_state;
extern void SSL_set_connect_state(SSL *);
%rename(ssl_get_shutdown) SSL_get_shutdown;
extern int SSL_get_shutdown(CONST SSL *);
%rename(ssl_set_shutdown) SSL_set_shutdown;
extern void SSL_set_shutdown(SSL *, int);
%rename(ssl_shutdown) SSL_shutdown;
extern int SSL_shutdown(SSL *);
%rename(ssl_clear) SSL_clear;
extern int SSL_clear(SSL *);
%rename(ssl_do_handshake) SSL_do_handshake;
extern int SSL_do_handshake(SSL *);
%rename(ssl_renegotiate) SSL_renegotiate;
extern int SSL_renegotiate(SSL *);
%rename(ssl_pending) SSL_pending;
extern int SSL_pending(CONST SSL *);

%rename(ssl_get_peer_cert) SSL_get_peer_certificate;
extern X509 *SSL_get_peer_certificate(CONST SSL *);
%rename(ssl_get_current_cipher) SSL_get_current_cipher;
extern SSL_CIPHER *SSL_get_current_cipher(CONST SSL *);
%rename(ssl_get_verify_mode) SSL_get_verify_mode;
extern int SSL_get_verify_mode(CONST SSL *);
%rename(ssl_get_verify_depth) SSL_get_verify_depth;
extern int SSL_get_verify_depth(CONST SSL *);
%rename(ssl_get_verify_result) SSL_get_verify_result;
extern long SSL_get_verify_result(CONST SSL *);
%rename(ssl_get_ssl_ctx) SSL_get_SSL_CTX;
extern SSL_CTX *SSL_get_SSL_CTX(CONST SSL *);
%rename(ssl_get_default_session_timeout) SSL_get_default_timeout;
extern long SSL_get_default_timeout(CONST SSL *);

%rename(ssl_set_cipher_list) SSL_set_cipher_list;
extern int SSL_set_cipher_list(SSL *, const char *);
%rename(ssl_get_cipher_list) SSL_get_cipher_list;
extern const char *SSL_get_cipher_list(CONST SSL *, int);

%rename(ssl_cipher_get_name) SSL_CIPHER_get_name;
extern const char *SSL_CIPHER_get_name(CONST SSL_CIPHER *);
%rename(ssl_cipher_get_version) SSL_CIPHER_get_version;
extern char *SSL_CIPHER_get_version(CONST SSL_CIPHER *);

%rename(ssl_get_session) SSL_get_session;
extern SSL_SESSION *SSL_get_session(CONST SSL *);
%rename(ssl_get1_session) SSL_get1_session;
extern SSL_SESSION *SSL_get1_session(SSL *);
%rename(ssl_set_session) SSL_set_session;
extern int SSL_set_session(SSL *, SSL_SESSION *);
%rename(ssl_session_free) SSL_SESSION_free;
extern void SSL_SESSION_free(SSL_SESSION *);
%rename(ssl_session_print) SSL_SESSION_print;
extern int SSL_SESSION_print(BIO *, CONST SSL_SESSION *);
%rename(ssl_session_set_timeout) SSL_SESSION_set_timeout;
extern long SSL_SESSION_set_timeout(SSL_SESSION *, long);
%rename(ssl_session_get_timeout) SSL_SESSION_get_timeout;
extern long SSL_SESSION_get_timeout(CONST SSL_SESSION *);

%constant int ssl_error_none              = SSL_ERROR_NONE;
%constant int ssl_error_ssl               = SSL_ERROR_SSL;
%constant int ssl_error_want_read         = SSL_ERROR_WANT_READ;
%constant int ssl_error_want_write        = SSL_ERROR_WANT_WRITE;
%constant int ssl_error_want_x509_lookup  = SSL_ERROR_WANT_X509_LOOKUP;
%constant int ssl_error_syscall           = SSL_ERROR_SYSCALL;
%constant int ssl_error_zero_return       = SSL_ERROR_ZERO_RETURN;
%constant int ssl_error_want_connect      = SSL_ERROR_WANT_CONNECT;

%constant int SSL_VERIFY_NONE                 = 0x00;
%constant int SSL_VERIFY_PEER                 = 0x01;
%constant int SSL_VERIFY_FAIL_IF_NO_PEER_CERT = 0x02;
%constant int SSL_VERIFY_CLIENT_ONCE          = 0x04;

%constant int SSL_ST_CONNECT                  = 0x1000;
%constant int SSL_ST_ACCEPT                   = 0x2000;
%constant int SSL_ST_MASK                     = 0x0FFF;
%constant int SSL_ST_INIT                     = (SSL_ST_CONNECT|SSL_ST_ACCEPT);
%constant int SSL_ST_BEFORE                   = 0x4000;
%constant int SSL_ST_OK                       = 0x03;
%constant int SSL_ST_RENEGOTIATE              = (0x04|SSL_ST_INIT);

%constant int SSL_CB_LOOP                     = 0x01;
%constant int SSL_CB_EXIT                     = 0x02;
%constant int SSL_CB_READ                     = 0x04;
%constant int SSL_CB_WRITE                    = 0x08;
%constant int SSL_CB_ALERT                    = 0x4000; /* used in callback */
%constant int SSL_CB_READ_ALERT               = (SSL_CB_ALERT|SSL_CB_READ);
%constant int SSL_CB_WRITE_ALERT              = (SSL_CB_ALERT|SSL_CB_WRITE);
%constant int SSL_CB_ACCEPT_LOOP              = (SSL_ST_ACCEPT|SSL_CB_LOOP);
%constant int SSL_CB_ACCEPT_EXIT              = (SSL_ST_ACCEPT|SSL_CB_EXIT);
%constant int SSL_CB_CONNECT_LOOP             = (SSL_ST_CONNECT|SSL_CB_LOOP);
%constant int SSL_CB_CONNECT_EXIT             = (SSL_ST_CONNECT|SSL_CB_EXIT);
%constant int SSL_CB_HANDSHAKE_START          = 0x10;
%constant int SSL_CB_HANDSHAKE_DONE           = 0x20;

%constant int SSL_SENT_SHUTDOWN              = 1;
%constant int SSL_RECEIVED_SHUTDOWN          = 2;

%constant int SSL_SESS_CACHE_OFF            = 0x000;
%constant int SSL_SESS_CACHE_CLIENT         = 0x001;
%constant int SSL_SESS_CACHE_SERVER         = 0x002;
%constant int SSL_SESS_CACHE_BOTH           = (SSL_SESS_CACHE_CLIENT|SSL_SESS_CACHE_SERVER);

%constant int SSL_OP_ALL                  = 0x00000FFFL;

%constant int SSL_OP_NO_SSLv2             = 0x01000000L;
%constant int SSL_OP_NO_SSLv3             = 0x02000000L;
%constant int SSL_OP_NO_TLSv1             = 0x04000000L;
%constant int SSL_OP_DONT_INSERT_EMPTY_FRAGMENTS = 0x00000800L;

%constant int SSL_MODE_ENABLE_PARTIAL_WRITE = SSL_MODE_ENABLE_PARTIAL_WRITE;
%constant int SSL_MODE_ACCEPT_MOVING_WRITE_BUFFER = SSL_MODE_ENABLE_PARTIAL_WRITE;
%constant int SSL_MODE_AUTO_RETRY           = SSL_MODE_AUTO_RETRY;

%inline %{
static PyObject *_ssl_err;

void ssl_init(PyObject *ssl_err) {
    SSL_library_init();
    SSL_load_error_strings();
    Py_INCREF(ssl_err);
    _ssl_err = ssl_err;
}

void ssl_ctx_passphrase_callback(SSL_CTX *ctx, PyObject *pyfunc) {
    SSL_CTX_set_default_passwd_cb(ctx, passphrase_callback);
    SSL_CTX_set_default_passwd_cb_userdata(ctx, (void *)pyfunc);
    Py_INCREF(pyfunc);
}

int ssl_ctx_use_x509(SSL_CTX *ctx, X509 *x) {
    int i;
    
    if (!(i = SSL_CTX_use_certificate(ctx, x))) {
        PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    return i;

}

int ssl_ctx_use_cert(SSL_CTX *ctx, char *file) {
    int i;
    
    if (!(i = SSL_CTX_use_certificate_file(ctx, file, SSL_FILETYPE_PEM))) {
        PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    return i;
}

int ssl_ctx_use_cert_chain(SSL_CTX *ctx, char *file) {
    int i;

    if (!(i = SSL_CTX_use_certificate_chain_file(ctx, file))) {
        PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    return i;
}


int ssl_ctx_use_privkey(SSL_CTX *ctx, char *file) {
    int i;
    
    if (!(i = SSL_CTX_use_PrivateKey_file(ctx, file, SSL_FILETYPE_PEM))) {
        PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    return i;
}

int ssl_ctx_use_rsa_privkey(SSL_CTX *ctx, RSA *rsakey) {
    int i;

    if (!(i = SSL_CTX_use_RSAPrivateKey(ctx, rsakey))) {
        PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    return i;
}

int ssl_ctx_use_pkey_privkey(SSL_CTX *ctx, EVP_PKEY *pkey) {
    int i;

    if (!(i = SSL_CTX_use_PrivateKey(ctx, pkey))) {
        PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    return i;
}


int ssl_ctx_check_privkey(SSL_CTX *ctx) {
    int ret;
    
    if (!(ret = SSL_CTX_check_private_key(ctx))) {
        PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    return ret;
}

void ssl_ctx_set_client_CA_list_from_file(SSL_CTX *ctx, const char *ca_file) {
    SSL_CTX_set_client_CA_list(ctx, SSL_load_client_CA_file(ca_file));
}

void ssl_ctx_set_verify_default(SSL_CTX *ctx, int mode) {
    SSL_CTX_set_verify(ctx, mode, NULL);
}

void ssl_ctx_set_verify(SSL_CTX *ctx, int mode, PyObject *pyfunc) {
    Py_XDECREF(ssl_verify_cb_func);
    Py_INCREF(pyfunc);
    ssl_verify_cb_func = pyfunc;
    SSL_CTX_set_verify(ctx, mode, ssl_verify_callback);
}

int ssl_ctx_set_session_id_context(SSL_CTX *ctx, PyObject *sid_ctx) {
    const void *buf;
    int len;

    if (m2_PyObject_AsReadBufferInt(sid_ctx, &buf, &len) == -1)
        return -1;

    return SSL_CTX_set_session_id_context(ctx, buf, len);
}

void ssl_ctx_set_info_callback(SSL_CTX *ctx, PyObject *pyfunc) {
    Py_XDECREF(ssl_info_cb_func);
    Py_INCREF(pyfunc);
    ssl_info_cb_func = pyfunc;
    SSL_CTX_set_info_callback(ctx, ssl_info_callback);
}

long ssl_ctx_set_tmp_dh(SSL_CTX *ctx, DH* dh) {
    return SSL_CTX_set_tmp_dh(ctx, dh);
}

void ssl_ctx_set_tmp_dh_callback(SSL_CTX *ctx,  PyObject *pyfunc) {
    Py_XDECREF(ssl_set_tmp_dh_cb_func);
    Py_INCREF(pyfunc);
    ssl_set_tmp_dh_cb_func = pyfunc;
    SSL_CTX_set_tmp_dh_callback(ctx, ssl_set_tmp_dh_callback);
}

long ssl_ctx_set_tmp_rsa(SSL_CTX *ctx, RSA* rsa) {
    return SSL_CTX_set_tmp_rsa(ctx, rsa);
}

void ssl_ctx_set_tmp_rsa_callback(SSL_CTX *ctx,  PyObject *pyfunc) {
    Py_XDECREF(ssl_set_tmp_rsa_cb_func);
    Py_INCREF(pyfunc);
    ssl_set_tmp_rsa_cb_func = pyfunc;
    SSL_CTX_set_tmp_rsa_callback(ctx, ssl_set_tmp_rsa_callback);
}

int ssl_ctx_load_verify_locations(SSL_CTX *ctx, const char *cafile, const char *capath) {
    return SSL_CTX_load_verify_locations(ctx, cafile, capath);
}

/* SSL_CTX_set_options is a macro. */
long ssl_ctx_set_options(SSL_CTX *ctx, long op) {
    return SSL_CTX_set_options(ctx, op);
}

int bio_set_ssl(BIO *bio, SSL *ssl, int flag) {
    SSL_set_mode(ssl, SSL_MODE_AUTO_RETRY);
    return BIO_ctrl(bio, BIO_C_SET_SSL, flag, (char *)ssl);
}

long ssl_set_mode(SSL *ssl, long mode) {
    return SSL_set_mode(ssl, mode);
}

long ssl_get_mode(SSL *ssl) {
    return SSL_get_mode(ssl);
}

void ssl_set_client_CA_list_from_file(SSL *ssl, const char *ca_file) {
    SSL_set_client_CA_list(ssl, SSL_load_client_CA_file(ca_file));
}

void ssl_set_client_CA_list_from_context(SSL *ssl, SSL_CTX *ctx) {
    SSL_set_client_CA_list(ssl, SSL_CTX_get_client_CA_list(ctx));
}

int ssl_set_session_id_context(SSL *ssl, PyObject *sid_ctx) {
    const void *buf;
    int len;

    if (m2_PyObject_AsReadBufferInt(sid_ctx, &buf, &len) == -1)
        return -1;

    return SSL_set_session_id_context(ssl, buf, len);
}

int ssl_set_fd(SSL *ssl, int fd) {
    int ret;
    
    if (!(ret = SSL_set_fd(ssl, fd))) {
        PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    return ret;
}

PyObject *ssl_accept(SSL *ssl) {
    PyObject *obj = NULL;
    int r, err;

    Py_BEGIN_ALLOW_THREADS
    r = SSL_accept(ssl);
    Py_END_ALLOW_THREADS


    switch (SSL_get_error(ssl, r)) {
        case SSL_ERROR_NONE:
        case SSL_ERROR_ZERO_RETURN:
            obj = PyInt_FromLong((long)1);
            break;
        case SSL_ERROR_WANT_WRITE:
        case SSL_ERROR_WANT_READ:
            obj = PyInt_FromLong((long)0);
            break;
        case SSL_ERROR_SSL:
            PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
            obj = NULL;
            break;
        case SSL_ERROR_SYSCALL:
            err = ERR_get_error();
            if (err)
                PyErr_SetString(_ssl_err, ERR_reason_error_string(err));
            else if (r == 0)
                PyErr_SetString(_ssl_err, "unexpected eof");
            else if (r == -1)
                PyErr_SetFromErrno(_ssl_err);
            obj = NULL;
            break;
    }


    return obj;
}

PyObject *ssl_connect(SSL *ssl) {
    PyObject *obj = NULL;
    int r, err;

    Py_BEGIN_ALLOW_THREADS
    r = SSL_connect(ssl);
    Py_END_ALLOW_THREADS

    
    switch (SSL_get_error(ssl, r)) {
        case SSL_ERROR_NONE:
        case SSL_ERROR_ZERO_RETURN:
            obj = PyInt_FromLong((long)1);
            break;
        case SSL_ERROR_WANT_WRITE:
        case SSL_ERROR_WANT_READ:
            obj = PyInt_FromLong((long)0);
            break;
        case SSL_ERROR_SSL:
            PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
            obj = NULL;
            break;
        case SSL_ERROR_SYSCALL:
            err = ERR_get_error();
            if (err)
                PyErr_SetString(_ssl_err, ERR_reason_error_string(err));
            else if (r == 0)
                PyErr_SetString(_ssl_err, "unexpected eof");
            else if (r == -1)
                PyErr_SetFromErrno(_ssl_err);
            obj = NULL;
            break;
    }
    
    
    return obj;
}

void ssl_set_shutdown1(SSL *ssl, int mode) {
    SSL_set_shutdown(ssl, mode);
}

PyObject *ssl_read(SSL *ssl, int num) {
    PyObject *obj = NULL;
    void *buf;
    int r, err;

    if (!(buf = PyMem_Malloc(num))) {
        PyErr_SetString(PyExc_MemoryError, "ssl_read");
        return NULL;
    }


    Py_BEGIN_ALLOW_THREADS
    r = SSL_read(ssl, buf, num);
    Py_END_ALLOW_THREADS


    switch (SSL_get_error(ssl, r)) {
        case SSL_ERROR_NONE:
        case SSL_ERROR_ZERO_RETURN:
            buf = PyMem_Realloc(buf, r);
            obj = PyString_FromStringAndSize(buf, r);
            break;
        case SSL_ERROR_WANT_WRITE:
        case SSL_ERROR_WANT_READ:
        case SSL_ERROR_WANT_X509_LOOKUP:
            Py_INCREF(Py_None);
            obj = Py_None;
            break;
        case SSL_ERROR_SSL:
            PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
            obj = NULL;
            break;
        case SSL_ERROR_SYSCALL:
            err = ERR_get_error();
            if (err)
                PyErr_SetString(_ssl_err, ERR_reason_error_string(err));
            else if (r == 0)
                PyErr_SetString(_ssl_err, "unexpected eof");
            else if (r == -1)
                PyErr_SetFromErrno(_ssl_err);
            obj = NULL;
            break;
    }
    PyMem_Free(buf);


    return obj;
}

PyObject *ssl_read_nbio(SSL *ssl, int num) {
    PyObject *obj = NULL;
    void *buf;
    int r, err;


    if (!(buf = PyMem_Malloc(num))) {
        PyErr_SetString(PyExc_MemoryError, "ssl_read");
        return NULL;
    }
    
    
    Py_BEGIN_ALLOW_THREADS
    r = SSL_read(ssl, buf, num);
    Py_END_ALLOW_THREADS
    
    
    switch (SSL_get_error(ssl, r)) {
        case SSL_ERROR_NONE:
        case SSL_ERROR_ZERO_RETURN:
            buf = PyMem_Realloc(buf, r);
            obj = PyString_FromStringAndSize(buf, r);
            break;
        case SSL_ERROR_WANT_WRITE:
        case SSL_ERROR_WANT_READ:
        case SSL_ERROR_WANT_X509_LOOKUP:
            Py_INCREF(Py_None);
            obj = Py_None;
            break;
        case SSL_ERROR_SSL:
            PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
            obj = NULL;
            break;
        case SSL_ERROR_SYSCALL:
            err = ERR_get_error();
            if (err)
                PyErr_SetString(_ssl_err, ERR_reason_error_string(err));
            else if (r == 0)
                PyErr_SetString(_ssl_err, "unexpected eof");
            else if (r == -1)
                PyErr_SetFromErrno(_ssl_err);
            obj = NULL;
            break;
    }
    PyMem_Free(buf);
    
    
    return obj;
}

int ssl_write(SSL *ssl, PyObject *blob) {
    const void *buf;
    int len, r, err, ret;


    if (m2_PyObject_AsReadBufferInt(blob, &buf, &len) == -1) {
        return -1;
    }

    
    Py_BEGIN_ALLOW_THREADS
    r = SSL_write(ssl, buf, len);
    Py_END_ALLOW_THREADS


    switch (SSL_get_error(ssl, r)) {
        case SSL_ERROR_NONE:
        case SSL_ERROR_ZERO_RETURN:
            ret = r;
            break;
        case SSL_ERROR_WANT_WRITE:
        case SSL_ERROR_WANT_READ:
        case SSL_ERROR_WANT_X509_LOOKUP:
            ret = -1;
            break;
        case SSL_ERROR_SSL:
            PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
            ret = -1;
            break;
        case SSL_ERROR_SYSCALL:
            err = ERR_get_error();
            if (err)
                PyErr_SetString(_ssl_err, ERR_reason_error_string(ERR_get_error()));
            else if (r == 0)
                PyErr_SetString(_ssl_err, "unexpected eof");
            else if (r == -1)
                PyErr_SetFromErrno(_ssl_err);
        default:
            ret = -1;
    }
    
    
    return ret;
}

int ssl_write_nbio(SSL *ssl, PyObject *blob) {
    const void *buf;
    int len, r, err, ret;


    if (m2_PyObject_AsReadBufferInt(blob, &buf, &len) == -1) {
        return -1;
    }

    
    Py_BEGIN_ALLOW_THREADS
    r = SSL_write(ssl, buf, len);
    Py_END_ALLOW_THREADS
    
    
    switch (SSL_get_error(ssl, r)) {
        case SSL_ERROR_NONE:
        case SSL_ERROR_ZERO_RETURN:
            ret = r;
            break;
        case SSL_ERROR_WANT_WRITE:
        case SSL_ERROR_WANT_READ:
        case SSL_ERROR_WANT_X509_LOOKUP:
            ret = -1;
            break;
        case SSL_ERROR_SSL:
            ret = -1;
            break;
        case SSL_ERROR_SYSCALL:
            err = ERR_get_error();
            if (err)
                PyErr_SetString(_ssl_err, ERR_reason_error_string(err));
            else if (r == 0)
                PyErr_SetString(_ssl_err, "unexpected eof");
            else if (r == -1)
                PyErr_SetFromErrno(_ssl_err);
        default:
            ret = -1;
    }
    
    
    return ret;
}

int ssl_cipher_get_bits(SSL_CIPHER *c) {
    return SSL_CIPHER_get_bits(c, NULL);
}

STACK *ssl_get_ciphers(SSL *ssl) {
    return (STACK *)SSL_get_ciphers(ssl);
}

int sk_ssl_cipher_num(STACK *stack) {
    return sk_num(stack);
}

SSL_CIPHER *sk_ssl_cipher_value(STACK *stack, int idx) {
    return (SSL_CIPHER *)sk_value(stack, idx);
}

STACK *ssl_get_peer_cert_chain(SSL *ssl) {
    return (STACK *)SSL_get_peer_cert_chain(ssl);
}

int sk_x509_num(STACK *stack) {
    return sk_num(stack);
}

X509 *sk_x509_value(STACK *stack, int idx) {
    return (X509 *)sk_value(stack, idx);
}

void i2d_ssl_session(BIO *bio, SSL_SESSION *sess) {
    i2d_SSL_SESSION_bio(bio, sess);
}

SSL_SESSION *ssl_session_read_pem(BIO *bio) {
    return PEM_read_bio_SSL_SESSION(bio, NULL, NULL, NULL);
}

int ssl_session_write_pem(SSL_SESSION *sess, BIO *bio) {
    return PEM_write_bio_SSL_SESSION(bio, sess);
}

int ssl_ctx_set_session_cache_mode(SSL_CTX *ctx, int mode)
{
    return SSL_CTX_set_session_cache_mode(ctx, mode);
}

int ssl_ctx_get_session_cache_mode(SSL_CTX *ctx)
{
    return SSL_CTX_get_session_cache_mode(ctx);
}

static long ssl_ctx_set_cache_size(SSL_CTX *ctx, long arg)
{
  return SSL_CTX_sess_set_cache_size(ctx, arg);
}

int ssl_is_init_finished(SSL *ssl)
{
  return SSL_is_init_finished(ssl);
}
%}

