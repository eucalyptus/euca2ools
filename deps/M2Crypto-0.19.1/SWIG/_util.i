/* Copyright (c) 1999-2002 Ng Pheng Siong. All rights reserved. */
/* $Id: _util.i 522 2007-05-08 22:21:51Z heikki $ */

%{
#include <openssl/x509v3.h>
%}

%inline %{
static PyObject *_util_err;

void util_init(PyObject *util_err) {
    Py_INCREF(util_err);
    _util_err = util_err;
}
    
PyObject *util_hex_to_string(PyObject *blob) {
    PyObject *obj;
    const void *buf;
    char *ret;
    Py_ssize_t len;

    if (PyObject_AsReadBuffer(blob, &buf, &len) == -1)
        return NULL;

    ret = hex_to_string((unsigned char *)buf, len);
    if (!ret) {
        PyErr_SetString(_util_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    obj = PyString_FromString(ret);
    OPENSSL_free(ret);
    return obj;
}

PyObject *util_string_to_hex(PyObject *blob) {
    PyObject *obj;
    const void *buf;
    unsigned char *ret;
    Py_ssize_t len0;
    long len;

    if (PyObject_AsReadBuffer(blob, &buf, &len0) == -1)
        return NULL;

    len = len0;
    ret = string_to_hex((char *)buf, &len);
    if (ret == NULL) {
        PyErr_SetString(_util_err, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }
    obj = PyString_FromStringAndSize(ret, len);
    OPENSSL_free(ret);
    return obj;
}
%}
