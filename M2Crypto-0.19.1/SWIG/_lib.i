/* Copyright (c) 1999-2004 Ng Pheng Siong. All rights reserved. */
/* $Id: _lib.i 607 2008-06-12 04:59:04Z heikki $ */

%{
#include <openssl/dh.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/rsa.h>
#include <openssl/ssl.h>
#include <openssl/x509.h>
#include <ceval.h>

/* Blob interface. Deprecated. */

Blob *blob_new(int len, const char *errmsg) {
    
    Blob *blob;
    if (!(blob=(Blob *)PyMem_Malloc(sizeof(Blob)))){
        PyErr_SetString(PyExc_MemoryError, errmsg);
        return NULL;
    }
    if (!(blob->data=(unsigned char *)PyMem_Malloc(len))) {
        PyMem_Free(blob);
        PyErr_SetString(PyExc_MemoryError, errmsg);
        return NULL;
    }
    blob->len=len;
    return blob;
}

Blob *blob_copy(Blob *from, const char *errmsg) {
    Blob *blob=blob_new(from->len, errmsg);
    if (!blob) {
        PyErr_SetString(PyExc_MemoryError, errmsg);
        return NULL;
    }
    memcpy(blob->data, from->data, from->len);
    return blob;
}

void blob_free(Blob *blob) {
    PyMem_Free(blob->data);
    PyMem_Free(blob);
}


/* Python helpers. */

%}
%ignore m2_PyObject_AsReadBufferInt;
%ignore m2_PyString_AsStringAndSizeInt;
%{
static int
m2_PyObject_AsReadBufferInt(PyObject *obj, const void **buffer,
                int *buffer_len)
{
    int ret;
    Py_ssize_t len;

    ret = PyObject_AsReadBuffer(obj, buffer, &len);
    if (ret)
        return ret;
    if (len > INT_MAX) {
        PyErr_SetString(PyExc_ValueError, "object too large");
        return -1;
    }
    *buffer_len = len;
    return 0;
}

static int
m2_PyString_AsStringAndSizeInt(PyObject *obj, char **s, int *len)
{
    int ret;
    Py_ssize_t len2;

    ret = PyString_AsStringAndSize(obj, s, &len2);
    if (ret)
       return ret;
    if (len2 > INT_MAX) {
       PyErr_SetString(PyExc_ValueError, "string too large");
       return -1;
    }
    *len = len2;
    return 0;
}


/* C callbacks invoked by OpenSSL; these in turn call back into 
Python. */

int ssl_verify_callback(int ok, X509_STORE_CTX *ctx) {
    PyObject *argv, *ret;
    PyObject *_x509_store_ctx_swigptr=0, *_x509_store_ctx_obj=0, *_x509_store_ctx_inst=0, *_klass=0;
    PyObject *_x509=0, *_ssl_ctx=0;
    SSL *ssl;
    SSL_CTX *ssl_ctx;
    X509 *x509;
    int errnum, errdepth;
    int cret;
    int new_style_callback = 0, warning_raised_exception=0;
    PyGILState_STATE gilstate;

    ssl = (SSL *)X509_STORE_CTX_get_app_data(ctx);

    gilstate = PyGILState_Ensure();

    if (PyMethod_Check(ssl_verify_cb_func)) {
        PyObject *func;
        PyCodeObject *code;
        func = PyMethod_Function(ssl_verify_cb_func);
        code = (PyCodeObject *) PyFunction_GetCode(func);
        if (code && code->co_argcount == 3) { /* XXX Python internals */
            new_style_callback = 1;
        }
    } else if (PyFunction_Check(ssl_verify_cb_func)) {
        PyCodeObject *code = (PyCodeObject *) PyFunction_GetCode(ssl_verify_cb_func);
        if (code && code->co_argcount == 2) { /* XXX Python internals */
            new_style_callback = 1;
        }    
    } else {
        /* XXX There are lots of other callable types, but we will assume
         * XXX that any other type of callable uses the new style callback,
         * XXX although this is not entirely safe assumption.
         */
        new_style_callback = 1;
    }
    
    if (new_style_callback) {
        PyObject *x509mod = PyDict_GetItemString(PyImport_GetModuleDict(), "M2Crypto.X509");
        _klass = PyObject_GetAttrString(x509mod, "X509_Store_Context");
    
        _x509_store_ctx_swigptr = SWIG_NewPointerObj((void *)ctx, SWIGTYPE_p_X509_STORE_CTX, 0);
        _x509_store_ctx_obj = Py_BuildValue("(Oi)", _x509_store_ctx_swigptr, 0);
        _x509_store_ctx_inst = PyInstance_New(_klass, _x509_store_ctx_obj, NULL);
        argv = Py_BuildValue("(iO)", ok, _x509_store_ctx_inst);
    } else {
        if (PyErr_Warn(PyExc_DeprecationWarning, "Old style callback, use cb_func(ok, store) instead")) {
            warning_raised_exception = 1;
        }
       
        x509 = X509_STORE_CTX_get_current_cert(ctx);
        errnum = X509_STORE_CTX_get_error(ctx);
        errdepth = X509_STORE_CTX_get_error_depth(ctx);
    
        ssl = (SSL *)X509_STORE_CTX_get_app_data(ctx);
        ssl_ctx = SSL_get_SSL_CTX(ssl);
    
        _x509 = SWIG_NewPointerObj((void *)x509, SWIGTYPE_p_X509, 0);
        _ssl_ctx = SWIG_NewPointerObj((void *)ssl_ctx, SWIGTYPE_p_SSL_CTX, 0);
        argv = Py_BuildValue("(OOiii)", _ssl_ctx, _x509, errnum, errdepth, ok);    
    }

    if (!warning_raised_exception) {
        ret = PyEval_CallObject(ssl_verify_cb_func, argv);
    } else {
        ret = 0;
    }

    if (!ret) {
        /* Got an exception in PyEval_CallObject(), let's fail verification
         * to be safe.
         */
        cret = 0;   
    } else {
        cret = (int)PyInt_AsLong(ret);
    }
    Py_XDECREF(ret);
    Py_XDECREF(argv);
    if (new_style_callback) {
        Py_XDECREF(_x509_store_ctx_inst);
        Py_XDECREF(_x509_store_ctx_obj);
        Py_XDECREF(_x509_store_ctx_swigptr);
        Py_XDECREF(_klass);
    } else {
        Py_XDECREF(_x509);
        Py_XDECREF(_ssl_ctx);
    }

    PyGILState_Release(gilstate);

    return cret;
}

void ssl_info_callback(const SSL *s, int where, int ret) {
    PyObject *argv, *retval, *_SSL;
    PyGILState_STATE gilstate;

    gilstate = PyGILState_Ensure();

    _SSL = SWIG_NewPointerObj((void *)s, SWIGTYPE_p_SSL, 0);
    argv = Py_BuildValue("(iiO)", where, ret, _SSL);
    
    retval = PyEval_CallObject(ssl_info_cb_func, argv);

    Py_XDECREF(retval);
    Py_XDECREF(argv);
    Py_XDECREF(_SSL);

    PyGILState_Release(gilstate);
}

DH *ssl_set_tmp_dh_callback(SSL *ssl, int is_export, int keylength) {
    PyObject *argv, *ret, *_ssl;
    DH *dh;
    PyGILState_STATE gilstate;

    gilstate = PyGILState_Ensure();

    _ssl = SWIG_NewPointerObj((void *)ssl, SWIGTYPE_p_SSL, 0);
    argv = Py_BuildValue("(Oii)", _ssl, is_export, keylength);

    ret = PyEval_CallObject(ssl_set_tmp_dh_cb_func, argv);

    if ((SWIG_ConvertPtr(ret, (void **)&dh, SWIGTYPE_p_DH, SWIG_POINTER_EXCEPTION | 0)) == -1)
      dh = NULL;
    Py_XDECREF(ret);
    Py_XDECREF(argv);
    Py_XDECREF(_ssl);

    PyGILState_Release(gilstate);

    return dh;
}

RSA *ssl_set_tmp_rsa_callback(SSL *ssl, int is_export, int keylength) {
    PyObject *argv, *ret, *_ssl;
    RSA *rsa;
    PyGILState_STATE gilstate;

    gilstate = PyGILState_Ensure();

    _ssl = SWIG_NewPointerObj((void *)ssl, SWIGTYPE_p_SSL, 0);
    argv = Py_BuildValue("(Oii)", _ssl, is_export, keylength);

    ret = PyEval_CallObject(ssl_set_tmp_rsa_cb_func, argv);

    if ((SWIG_ConvertPtr(ret, (void **)&rsa, SWIGTYPE_p_RSA, SWIG_POINTER_EXCEPTION | 0)) == -1)
      rsa = NULL;
    Py_XDECREF(ret);
    Py_XDECREF(argv);
    Py_XDECREF(_ssl);

    PyGILState_Release(gilstate);

    return rsa;
}

void gen_callback(int p, int n, void *arg) {
    PyObject *argv, *ret, *cbfunc;
 
    PyGILState_STATE gilstate;
    gilstate = PyGILState_Ensure();
    cbfunc = (PyObject *)arg;
    argv = Py_BuildValue("(ii)", p, n);
    ret = PyEval_CallObject(cbfunc, argv);
    Py_DECREF(argv);
    Py_XDECREF(ret);
    PyGILState_Release(gilstate);
}

int passphrase_callback(char *buf, int num, int v, void *arg) {
    int i;
    Py_ssize_t len;
    char *str;
    PyObject *argv, *ret, *cbfunc;

    /* NOTE: This should not acquire the GIL, as was discovered in bug 11813
     * by Keith Jackson:
     * "rsa_write_key in _rsa.i calls PEM_write_bio_RSAPrivateKey which if you
     * look at the openssl code calls the callback function passed into it. 
     * We never give up the GIL in rsa_write_key so trying to acquire it again
     * in the callback is going to result in deadlock"
     */
    cbfunc = (PyObject *)arg;
    argv = Py_BuildValue("(i)", v);
    ret = PyEval_CallObject(cbfunc, argv);
    Py_DECREF(argv);
    if (ret == NULL) {
        return -1;
    }
    if (!PyString_Check(ret)) {
        Py_DECREF(ret);
        return -1;
    }
    if ((len = PyString_Size(ret)) > num)
        len = num;
    str = PyString_AsString(ret); 
    for (i = 0; i < len; i++)
        buf[i] = str[i];
    Py_DECREF(ret);
    return len;
}
%}

%inline %{
void lib_init() {
    SSLeay_add_all_algorithms();
    ERR_load_ERR_strings();
}

/* Bignum routines that aren't not numerous enough to 
warrant a separate file. */

PyObject *bn_to_mpi(BIGNUM *bn) {
    int len;
    unsigned char *mpi;
    PyObject *pyo;  

    len = BN_bn2mpi(bn, NULL);
    if (!(mpi=(unsigned char *)PyMem_Malloc(len))) {
        PyErr_SetString(PyExc_RuntimeError, 
            ERR_error_string(ERR_get_error(), NULL));
        return NULL;
    }
    len=BN_bn2mpi(bn, mpi);
    pyo=PyString_FromStringAndSize((const char *)mpi, len);
    PyMem_Free(mpi);
    return pyo;
}

BIGNUM *mpi_to_bn(PyObject *value) {
    const void *vbuf;
    int vlen;

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    return BN_mpi2bn(vbuf, vlen, NULL);
}

PyObject *bn_to_bin(BIGNUM *bn) {
    int len;
    unsigned char *bin;
    PyObject *pyo;  

    len = BN_num_bytes(bn);
    if (!(bin=(unsigned char *)PyMem_Malloc(len))) {
      PyErr_SetString(PyExc_MemoryError, "bn_to_bin");
      return NULL;
    }
    BN_bn2bin(bn, bin);
    pyo=PyString_FromStringAndSize((const char *)bin, len);
    PyMem_Free(bin);
    return pyo;
}

BIGNUM *bin_to_bn(PyObject *value) {
    const void *vbuf;
    int vlen;

    if (m2_PyObject_AsReadBufferInt(value, &vbuf, &vlen) == -1)
        return NULL;

    return BN_bin2bn(vbuf, vlen, NULL);
}

PyObject *bn_to_hex(BIGNUM *bn) {
    char *hex;
    PyObject *pyo;  
    Py_ssize_t len;

    hex = BN_bn2hex(bn);
    if (!hex) {
        PyErr_SetString(PyExc_RuntimeError, 
              ERR_error_string(ERR_get_error(), NULL));
        OPENSSL_free(hex);
        return NULL;    
    }
    len = strlen(hex);
    pyo=PyString_FromStringAndSize(hex, len);
    OPENSSL_free(hex);
    return pyo;
}

BIGNUM *hex_to_bn(PyObject *value) {
    const void *vbuf;
    Py_ssize_t vlen;
    BIGNUM *bn;

    if (PyObject_AsReadBuffer(value, &vbuf, &vlen) == -1)
        return NULL;

    if ((bn=BN_new())==NULL) {
        PyErr_SetString(PyExc_MemoryError, "hex_to_bn");
        return NULL;
    }
    if (BN_hex2bn(&bn, (const char *)vbuf) <= 0) {
        PyErr_SetString(PyExc_RuntimeError, 
              ERR_error_string(ERR_get_error(), NULL));
        BN_free(bn);
        return NULL;
    }
    return bn;
}

BIGNUM *dec_to_bn(PyObject *value) {
    const void *vbuf;
    Py_ssize_t vlen;
    BIGNUM *bn;

    if (PyObject_AsReadBuffer(value, &vbuf, &vlen) == -1)
        return NULL;

    if ((bn=BN_new())==NULL) {
      PyErr_SetString(PyExc_MemoryError, "dec_to_bn");
      return NULL;
    }
    if ((BN_dec2bn(&bn, (const char *)vbuf) <= 0)) {
      PyErr_SetString(PyExc_RuntimeError, 
            ERR_error_string(ERR_get_error(), NULL));
      BN_free(bn);
      return NULL;
    }
    return bn;
}
%}


/* Various useful typemaps. */

%typemap(in) Blob * {
    Py_ssize_t len;

    if (!PyString_Check($input)) {
        PyErr_SetString(PyExc_TypeError, "expected PyString");
        return NULL;
    }
    len=PyString_Size($input);
    if (len > INT_MAX) {
        PyErr_SetString(PyExc_ValueError, "object too large");
        return -1;
    }
    $1=(Blob *)PyMem_Malloc(sizeof(Blob));
    if (!$1) {
        PyErr_SetString(PyExc_MemoryError, "malloc Blob");
        return NULL;
    }
    $1->data=(unsigned char *)PyString_AsString($input);
    $1->len=len;
}

%typemap(out) Blob * {
    if ($1==NULL) {
        Py_INCREF(Py_None);
        $result=Py_None;
    } else {
        $result=PyString_FromStringAndSize((const char *)$1->data, $1->len);
        PyMem_Free($1->data);
        PyMem_Free($1);
    }
}

%typemap(in) FILE * {
    if (!PyFile_Check($input)) {
        PyErr_SetString(PyExc_TypeError, "expected PyFile");
        return NULL;
    }
    $1=PyFile_AsFile($input);
}

%typemap(in) PyObject *pyfunc {
    if (!PyCallable_Check($input)) {
        PyErr_SetString(PyExc_TypeError, "expected PyCallable");
        return NULL;
    }
    $1=$input;
}

%typemap(in) PyObject *pyblob {
    if (!PyString_Check($input)) {
        PyErr_SetString(PyExc_TypeError, "expected PyString");
        return NULL;
    }
    $1=$input;
}

%typemap(in) PyObject * {
    $1=$input;
}

%typemap(out) PyObject * {
    $result=$1;
}

%typemap(out) int {
    $result=PyInt_FromLong($1);
    if (PyErr_Occurred()) SWIG_fail;
}

/* Pointer checks. */

%apply Pointer NONNULL { Blob * };


/* A bunch of "straight-thru" functions. */

%rename(err_print_errors_fp) ERR_print_errors_fp;
extern void ERR_print_errors_fp(FILE *);
%rename(err_print_errors) ERR_print_errors;
extern void ERR_print_errors(BIO *);
%rename(err_get_error) ERR_get_error;
extern unsigned long ERR_get_error(void);
%rename(err_peek_error) ERR_peek_error;
extern unsigned long ERR_peek_error(void);
%rename(err_lib_error_string) ERR_lib_error_string;
extern const char *ERR_lib_error_string(unsigned long);
%rename(err_func_error_string) ERR_func_error_string;
extern const char *ERR_func_error_string(unsigned long);
%rename(err_reason_error_string) ERR_reason_error_string;
extern const char *ERR_reason_error_string(unsigned long);
