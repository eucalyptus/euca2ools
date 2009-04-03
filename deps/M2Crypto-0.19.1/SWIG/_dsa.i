/* Copyright (c) 1999-2000 Ng Pheng Siong. All rights reserved. */
/* $Id: _dsa.i 522 2007-05-08 22:21:51Z heikki $ */

%{
#include <openssl/bn.h>
#include <openssl/err.h>
#include <openssl/pem.h>
#include <openssl/dsa.h>

PyObject *dsa_sig_get_r(DSA_SIG *dsa_sig) {
    return bn_to_mpi(dsa_sig->r);
}

PyObject *dsa_sig_get_s(DSA_SIG *dsa_sig) {
    return bn_to_mpi(dsa_sig->s);
}
%}

%apply Pointer NONNULL { DSA * };

%rename(dsa_new) DSA_new;
extern DSA *DSA_new(void);
%rename(dsa_free) DSA_free;
extern void DSA_free(DSA *);
%rename(dsa_size) DSA_size;
extern int DSA_size(const DSA *); /* assert(dsa->q); */
%rename(dsa_gen_key) DSA_generate_key;
extern int DSA_generate_key(DSA *);

%inline %{
static PyObject *_dsa_err;

void dsa_init(PyObject *dsa_err) {
    Py_INCREF(dsa_err);
    _dsa_err = dsa_err;
}

void genparam_callback(int p, int n, void *arg) {
    PyObject *argv, *ret, *cbfunc;

    cbfunc = (PyObject *)arg; 
    argv = Py_BuildValue("(ii)", p, n);
    ret = PyEval_CallObject(cbfunc, argv);
    PyErr_Clear();
    Py_DECREF(argv);
    Py_XDECREF(ret);
}

DSA *dsa_generate_parameters(int bits, PyObject *pyfunc) {
    DSA *dsa;

    Py_INCREF(pyfunc);
    dsa = DSA_generate_parameters(bits, NULL, 0, NULL, NULL, genparam_callback, (void *)pyfunc);
    Py_DECREF(pyfunc);
    if (!dsa)
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
    return dsa;
}

PyObject *dsa_get_p(DSA *dsa) {
    if (!dsa->p) {
        PyErr_SetString(_dsa_err, "'p' is unset");
        return NULL;
    }
    return bn_to_mpi(dsa->p);
}

PyObject *dsa_get_q(DSA *dsa) {
    if (!dsa->q) {
        PyErr_SetString(_dsa_err, "'q' is unset");
        return NULL;
    }
    return bn_to_mpi(dsa->q);
}

PyObject *dsa_get_g(DSA *dsa) {
    if (!dsa->g) {
        PyErr_SetString(_dsa_err, "'g' is unset");
        return NULL;
    }
    return bn_to_mpi(dsa->g);
}

PyObject *dsa_get_pub(DSA *dsa) {
    if (!dsa->pub_key) {
        PyErr_SetString(_dsa_err, "'pub' is unset");
        return NULL;
    }
    return bn_to_mpi(dsa->pub_key);
}

PyObject *dsa_get_priv(DSA *dsa) {
    if (!dsa->priv_key) {
        PyErr_SetString(_dsa_err, "'priv' is unset");
        return NULL;
    }
    return bn_to_mpi(dsa->priv_key);
}

PyObject *dsa_set_p(DSA *dsa, PyObject *value) {
    BIGNUM *bn;
    const void *vbuf;
    int vlen;

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    if (!(bn = BN_mpi2bn((unsigned char *)vbuf, vlen, NULL))) {
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    if (dsa->p)
        BN_free(dsa->p);
    dsa->p = bn;
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject *dsa_set_q(DSA *dsa, PyObject *value) {
    BIGNUM *bn;
    const void *vbuf;
    int vlen;

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    if (!(bn = BN_mpi2bn((unsigned char *)vbuf, vlen, NULL))) {
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    if (dsa->q)
        BN_free(dsa->q);
    dsa->q = bn;
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject *dsa_set_g(DSA *dsa, PyObject *value) {
    BIGNUM *bn;
    const void *vbuf;
    int vlen;

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    if (!(bn = BN_mpi2bn((unsigned char *)vbuf, vlen, NULL))) {
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    if (dsa->g)
        BN_free(dsa->g);
    dsa->g = bn;
    Py_INCREF(Py_None);
    return Py_None;
}

DSA *dsa_read_params(BIO *f, PyObject *pyfunc) {
    DSA *ret;

    Py_INCREF(pyfunc);
    ret = PEM_read_bio_DSAparams(f, NULL, passphrase_callback, (void *)pyfunc);
    Py_DECREF(pyfunc);
    return ret;
}

int dsa_write_params_bio(DSA* dsa, BIO* f) {
    return PEM_write_bio_DSAparams(f, dsa);
}

int dsa_write_key_bio(DSA* dsa, BIO* f, EVP_CIPHER *cipher, PyObject *pyfunc) {
    int ret;

    Py_INCREF(pyfunc);
    ret = PEM_write_bio_DSAPrivateKey(f, dsa, cipher, NULL, 0,
                                        passphrase_callback, (void *)pyfunc);
    Py_DECREF(pyfunc);
    return ret;
}

int dsa_write_key_bio_no_cipher(DSA* dsa, BIO* f, PyObject *pyfunc) {
    int ret;

    Py_INCREF(pyfunc);
    ret = PEM_write_bio_DSAPrivateKey(f, dsa, NULL, NULL, 0,
                                        passphrase_callback, (void *)pyfunc);
    Py_DECREF(pyfunc);
    return ret;
}

int dsa_write_pub_key_bio(DSA* dsa, BIO* f) {
    return PEM_write_bio_DSA_PUBKEY(f, dsa);
}

DSA *dsa_read_key(BIO *f, PyObject *pyfunc) {
    DSA *ret;

    Py_INCREF(pyfunc);
    ret = PEM_read_bio_DSAPrivateKey(f, NULL, passphrase_callback, (void *)pyfunc);
    Py_DECREF(pyfunc);
    return ret;
}

DSA *dsa_read_pub_key(BIO *f, PyObject *pyfunc) {
    DSA *ret;

    Py_INCREF(pyfunc);
    ret = PEM_read_bio_DSA_PUBKEY(f, NULL, passphrase_callback, (void *)pyfunc);
    Py_DECREF(pyfunc);
    return ret;
}

PyObject *dsa_sign(DSA *dsa, PyObject *value) {
    const void *vbuf;
    int vlen;
    PyObject *tuple;
    DSA_SIG *sig; 

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    if (!(sig = DSA_do_sign(vbuf, vlen, dsa))) {
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    if (!(tuple = PyTuple_New(2))) {
        DSA_SIG_free(sig);
        PyErr_SetString(PyExc_RuntimeError, "PyTuple_New() fails");
        return NULL;
    }
    PyTuple_SET_ITEM(tuple, 0, dsa_sig_get_r(sig));
    PyTuple_SET_ITEM(tuple, 1, dsa_sig_get_s(sig));
    DSA_SIG_free(sig);
    return tuple;
}

int dsa_verify(DSA *dsa, PyObject *value, PyObject *r, PyObject *s) {
    const void *vbuf, *rbuf, *sbuf;
    int vlen, rlen, slen;
    DSA_SIG *sig;
    int ret;

    if ((m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        || (m2_PyObject_AsReadBufferInt(r, &rbuf, &rlen) == -1)
        || (m2_PyObject_AsReadBufferInt(s, &sbuf, &slen) == -1))
        return -1;

    if (!(sig = DSA_SIG_new())) {
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
        return -1;
    }
    if (!(sig->r = BN_mpi2bn((unsigned char *)rbuf, rlen, NULL))) {
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
        DSA_SIG_free(sig);
        return -1;
    }
    if (!(sig->s = BN_mpi2bn((unsigned char *)sbuf, slen, NULL))) {
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
        DSA_SIG_free(sig);
        return -1;
    }
    ret = DSA_do_verify(vbuf, vlen, sig, dsa);
    DSA_SIG_free(sig);
    if (ret == -1)
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
    return ret;
}

PyObject *dsa_sign_asn1(DSA *dsa, PyObject *value) {
    const void *vbuf;
    int vlen;
    void *sigbuf;
    unsigned int siglen;
    PyObject *ret;

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    if (!(sigbuf = PyMem_Malloc(DSA_size(dsa)))) {
        PyErr_SetString(PyExc_MemoryError, "dsa_sign_asn1");
        return NULL;
    }
    if (!DSA_sign(0, vbuf, vlen, (unsigned char *)sigbuf, &siglen, dsa)) {
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
        PyMem_Free(sigbuf);
        return NULL;
    }
    ret = PyString_FromStringAndSize(sigbuf, siglen);
    PyMem_Free(sigbuf);
    return ret;
}

int dsa_verify_asn1(DSA *dsa, PyObject *value, PyObject *sig) {
    const void *vbuf; 
    void *sbuf;
    int vlen, slen, ret;

    if ((m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        || (m2_PyObject_AsReadBufferInt(sig, (const void **)&sbuf, &slen)
        == -1))
        return -1;

    if ((ret = DSA_verify(0, vbuf, vlen, sbuf, slen, dsa)) == -1)
        PyErr_SetString(_dsa_err, ERR_reason_error_string(ERR_get_error()));
    return ret;
}

int dsa_check_key(DSA *dsa) {
    return (dsa->pub_key) && (dsa->priv_key);
}

int dsa_check_pub_key(DSA *dsa) {
    return dsa->pub_key ? 1 : 0;
}

int dsa_keylen(DSA *dsa) {
    return BN_num_bits(dsa->p);
}

int dsa_type_check(DSA *dsa) {
    return 1;
}
%}

