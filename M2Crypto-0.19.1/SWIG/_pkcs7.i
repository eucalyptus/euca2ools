/* Copyright (c) 2000 Ng Pheng Siong. All rights reserved. */
/* $Id: _pkcs7.i 611 2008-07-22 07:53:18Z heikki $ */

%{
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/objects.h>
#include <openssl/pkcs7.h>
%}

%apply Pointer NONNULL { BIO * };
%apply Pointer NONNULL { EVP_CIPHER * };
%apply Pointer NONNULL { EVP_PKEY * };
%apply Pointer NONNULL { PKCS7 * };
%apply Pointer NONNULL { STACK * };
%apply Pointer NONNULL { X509 * };

%rename(pkcs7_new) PKCS7_new;
extern PKCS7 *PKCS7_new(void);
%rename(pkcs7_free) PKCS7_free;
extern void PKCS7_free(PKCS7 *);

/* S/MIME operation */
%constant int PKCS7_TEXT       = 0x1;
%constant int PKCS7_NOCERTS    = 0x2;
%constant int PKCS7_NOSIGS     = 0x4;
%constant int PKCS7_NOCHAIN    = 0x8;
%constant int PKCS7_NOINTERN   = 0x10;
%constant int PKCS7_NOVERIFY   = 0x20;
%constant int PKCS7_DETACHED   = 0x40;
%constant int PKCS7_BINARY     = 0x80;
%constant int PKCS7_NOATTR     = 0x100;

%constant int PKCS7_SIGNED            = NID_pkcs7_signed;
%constant int PKCS7_ENVELOPED         = NID_pkcs7_enveloped;
%constant int PKCS7_SIGNED_ENVELOPED  = NID_pkcs7_signedAndEnveloped;
%constant int PKCS7_DATA              = NID_pkcs7_data;

%inline %{
static PyObject *_pkcs7_err, *_smime_err;

void pkcs7_init(PyObject *pkcs7_err) {
    Py_INCREF(pkcs7_err);
    _pkcs7_err = pkcs7_err;
}

void smime_init(PyObject *smime_err) {
    Py_INCREF(smime_err);
    _smime_err = smime_err;
}

PKCS7 *pkcs7_encrypt(STACK *stack, BIO *bio, EVP_CIPHER *cipher, int flags) {
    return PKCS7_encrypt((STACK_OF(X509) *)stack, bio, cipher, flags);
}

PyObject *pkcs7_decrypt(PKCS7 *pkcs7, EVP_PKEY *pkey, X509 *cert, int flags) {
    int outlen;
    char *outbuf;
    BIO *bio;
    PyObject *ret; 

    if (!(bio=BIO_new(BIO_s_mem()))) {
        PyErr_SetString(PyExc_MemoryError, "pkcs7_decrypt");
        return NULL;
    }
    if (!PKCS7_decrypt(pkcs7, pkey, cert, bio, flags)) {
        PyErr_SetString(_pkcs7_err, ERR_reason_error_string(ERR_get_error()));
        BIO_free(bio);
        return NULL;
    }
    outlen = BIO_ctrl_pending(bio);
    if (!(outbuf=(char *)PyMem_Malloc(outlen))) {
        PyErr_SetString(PyExc_MemoryError, "pkcs7_decrypt");
        BIO_free(bio);
        return NULL;
    }
    BIO_read(bio, outbuf, outlen);
    ret = PyString_FromStringAndSize(outbuf, outlen);
    BIO_free(bio);
    PyMem_Free(outbuf);
    return ret;
}

PKCS7 *pkcs7_sign0(X509 *x509, EVP_PKEY *pkey, BIO *bio, int flags) {
    return PKCS7_sign(x509, pkey, NULL, bio, flags);
}

PKCS7 *pkcs7_sign1(X509 *x509, EVP_PKEY *pkey, STACK *stack, BIO *bio, int flags) {
    return PKCS7_sign(x509, pkey, (STACK_OF(X509) *)stack, bio, flags);
}

PyObject *pkcs7_verify1(PKCS7 *pkcs7, STACK *stack, X509_STORE *store, BIO *data, int flags) {
    int outlen;
    char *outbuf;
    BIO *bio;
    PyObject *ret; 

    if (!(bio=BIO_new(BIO_s_mem()))) {
        PyErr_SetString(PyExc_MemoryError, "pkcs7_verify1");
        return NULL;
    }
    if (!PKCS7_verify(pkcs7, (STACK_OF(X509) *)stack, store, data, bio, flags)) {
        PyErr_SetString(_pkcs7_err, ERR_reason_error_string(ERR_get_error()));
        BIO_free(bio);
        return NULL;
    }
    outlen = BIO_ctrl_pending(bio);
    if (!(outbuf=(char *)PyMem_Malloc(outlen))) {
        PyErr_SetString(PyExc_MemoryError, "pkcs7_verify1");
        BIO_free(bio);
        return NULL;
    }
    BIO_read(bio, outbuf, outlen);
    ret = PyString_FromStringAndSize(outbuf, outlen);
    BIO_free(bio);
    PyMem_Free(outbuf);
    return ret;
}

PyObject *pkcs7_verify0(PKCS7 *pkcs7, STACK *stack, X509_STORE *store, int flags) {
    return pkcs7_verify1(pkcs7, stack, store, NULL, flags);
}

int smime_write_pkcs7_multi(BIO *bio, PKCS7 *pkcs7, BIO *data, int flags) {
    return SMIME_write_PKCS7(bio, pkcs7, data, flags | PKCS7_DETACHED);
}

int smime_write_pkcs7(BIO *bio, PKCS7 *pkcs7, int flags) {
    return SMIME_write_PKCS7(bio, pkcs7, NULL, flags);
}

PyObject *smime_read_pkcs7(BIO *bio) {
    BIO *bcont = NULL;
    PKCS7 *p7;
    PyObject *tuple, *_p7, *_BIO;

    if (BIO_method_type(bio) == BIO_TYPE_MEM) {
        /* OpenSSL FAQ explains that this is needed for mem BIO to return EOF,
         * like file BIO does. Might need to do this for more mem BIOs but
         * not sure if that is safe, so starting with just this single place.
         */
        BIO_set_mem_eof_return(bio, 0);
    }

    if (!(p7=SMIME_read_PKCS7(bio, &bcont))) {
        PyErr_SetString(_smime_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    if (!(tuple=PyTuple_New(2))) {
        PyErr_SetString(PyExc_RuntimeError, "PyTuple_New() fails");
        return NULL;
    }
    _p7 = SWIG_NewPointerObj((void *)p7, SWIGTYPE_p_PKCS7, 0);
    PyTuple_SET_ITEM(tuple, 0, _p7);
    if (!bcont) {
        Py_INCREF(Py_None);
        PyTuple_SET_ITEM(tuple, 1, Py_None);
    } else {
        _BIO = SWIG_NewPointerObj((void *)bcont, SWIGTYPE_p_BIO, 0);
        PyTuple_SET_ITEM(tuple, 1, _BIO);
    }
    return tuple;
}

PKCS7 *pkcs7_read_bio(BIO *bio) {
    return PEM_read_bio_PKCS7(bio, NULL, NULL, NULL);
}

PKCS7 *pkcs7_read_bio_der(BIO *bio) {
    return d2i_PKCS7_bio(bio, NULL);
}

int pkcs7_write_bio(PKCS7 *pkcs7, BIO* bio) {
    return PEM_write_bio_PKCS7(bio, pkcs7);
}

int pkcs7_write_bio_der(PKCS7 *pkcs7, BIO *bio) {
    return i2d_PKCS7_bio(bio, pkcs7);
}

int pkcs7_type_nid(PKCS7 *pkcs7) {
    return OBJ_obj2nid(pkcs7->type);
}

const char *pkcs7_type_sn(PKCS7 *pkcs7) {
    return OBJ_nid2sn(OBJ_obj2nid(pkcs7->type));
}

int smime_crlf_copy(BIO *in, BIO *out) {
    return SMIME_crlf_copy(in, out, PKCS7_TEXT);
}

/* return STACK_OF(X509)* */     
STACK *pkcs7_get0_signers(PKCS7 *p7, STACK *certs, int flags) {     
    return PKCS7_get0_signers(p7, certs, flags);      
}

%}

