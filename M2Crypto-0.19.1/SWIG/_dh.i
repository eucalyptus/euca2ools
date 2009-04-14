/* Copyright (c) 1999 Ng Pheng Siong. All rights reserved. */
/* $Id: _dh.i 522 2007-05-08 22:21:51Z heikki $ */

%{
#include <openssl/bn.h>
#include <openssl/bio.h>
#include <openssl/err.h>
#include <openssl/pem.h>
#include <openssl/dh.h>
%}

%apply Pointer NONNULL { DH * };

%rename(dh_new) DH_new;
extern DH *DH_new(void);
%rename(dh_free) DH_free;
extern void DH_free(DH *);
%rename(dh_size) DH_size;
extern int DH_size(const DH *);
%rename(dh_generate_key) DH_generate_key;
extern int DH_generate_key(DH *);
%rename(dhparams_print) DHparams_print;
extern int DHparams_print(BIO *, const DH *);

%constant int dh_check_ok             = 0;
%constant int dh_check_p_not_prime    = DH_CHECK_P_NOT_PRIME;
%constant int dh_check_p_not_strong   = DH_CHECK_P_NOT_STRONG_PRIME;
%constant int dh_check_g_failed       = DH_UNABLE_TO_CHECK_GENERATOR;
%constant int dh_check_bad_g          = DH_NOT_SUITABLE_GENERATOR;

%constant DH_GENERATOR_2          = 2;
%constant DH_GENERATOR_5          = 5;

%inline %{
static PyObject *_dh_err;

void dh_init(PyObject *dh_err) {
    Py_INCREF(dh_err);
    _dh_err = dh_err;
}

int dh_type_check(DH *dh) {
    /* Our getting here means we passed Swig's type checking,
    XXX Still need to check the pointer for sanity? */
    return 1;
}

DH *dh_read_parameters(BIO *bio) {
    return PEM_read_bio_DHparams(bio, NULL, NULL, NULL);
}

void gendh_callback(int p, int n, void *arg) {
    PyObject *argv, *ret, *cbfunc;
 
    cbfunc = (PyObject *)arg;
    argv = Py_BuildValue("(ii)", p, n);
    ret = PyEval_CallObject(cbfunc, argv);
    PyErr_Clear();
    Py_DECREF(argv);
    Py_XDECREF(ret);
}

DH *dh_generate_parameters(int plen, int g, PyObject *pyfunc) {
    DH *dh;

    Py_INCREF(pyfunc);
    dh = DH_generate_parameters(plen, g, gendh_callback, (void *)pyfunc);
    Py_DECREF(pyfunc);
    if (!dh) 
        PyErr_SetString(_dh_err, ERR_reason_error_string(ERR_get_error()));
    return dh;
}

/* Note return value shenanigan. */
int dh_check(DH *dh) {
    int err;

    return (DH_check(dh, &err)) ? 0 : err;
}

PyObject *dh_compute_key(DH *dh, PyObject *pubkey) {
    const void *pkbuf;
    int pklen, klen;
    void *key;
    BIGNUM *pk;
    PyObject *ret;

    if (m2_PyObject_AsReadBufferInt(pubkey, &pkbuf, &pklen) == -1)
        return NULL;

    if (!(pk = BN_mpi2bn((unsigned char *)pkbuf, pklen, NULL))) {
        PyErr_SetString(_dh_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    if (!(key = PyMem_Malloc(DH_size(dh)))) {
        BN_free(pk);
        PyErr_SetString(PyExc_MemoryError, "dh_compute_key");
        return NULL;
    }
    if ((klen = DH_compute_key((unsigned char *)key, pk, dh)) == -1) {
        BN_free(pk);
        PyMem_Free(key);
        PyErr_SetString(_dh_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    ret = PyString_FromStringAndSize((const char *)key, klen);
    BN_free(pk);
    PyMem_Free(key);
    return ret;
}
        
PyObject *dh_get_p(DH *dh) {
    if (!dh->p) {
        PyErr_SetString(_dh_err, "'p' is unset");
        return NULL;
    }
    return bn_to_mpi(dh->p);
}

PyObject *dh_get_g(DH *dh) {
    if (!dh->g) {
        PyErr_SetString(_dh_err, "'g' is unset");
        return NULL;
    }
    return bn_to_mpi(dh->g);
}

PyObject *dh_get_pub(DH *dh) {
    if (!dh->pub_key) {
        PyErr_SetString(_dh_err, "'pub' is unset");
        return NULL;
    }
    return bn_to_mpi(dh->pub_key);
}

PyObject *dh_get_priv(DH *dh) {
    if (!dh->priv_key) {
        PyErr_SetString(_dh_err, "'priv' is unset");
        return NULL;
    }
    return bn_to_mpi(dh->priv_key);
}

PyObject *dh_set_p(DH *dh, PyObject *value) {
    BIGNUM *bn;
    const void *vbuf;
    int vlen;

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    if (!(bn = BN_mpi2bn((unsigned char *)vbuf, vlen, NULL))) {
        PyErr_SetString(_dh_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    if (dh->p)
        BN_free(dh->p);
    dh->p = bn;
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject *dh_set_g(DH *dh, PyObject *value) {
    BIGNUM *bn;
    const void *vbuf;
    int vlen;

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    if (!(bn = BN_mpi2bn((unsigned char *)vbuf, vlen, NULL))) {
        PyErr_SetString(_dh_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    if (dh->g)
        BN_free(dh->g);
    dh->g = bn;
    Py_INCREF(Py_None);
    return Py_None;
}
%}

