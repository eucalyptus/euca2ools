/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/* Copyright (c) 1999 Ng Pheng Siong. All rights reserved.
 *
 * Portions created by Open Source Applications Foundation (OSAF) are
 * Copyright (C) 2004-2005 OSAF. All Rights Reserved.
 * Author: Heikki Toivonen
*/
/* $Id: _bio.i 522 2007-05-08 22:21:51Z heikki $ */

%{
#include <openssl/bio.h>
%}

%apply Pointer NONNULL { BIO * };
%apply Pointer NONNULL { BIO_METHOD * };

%rename(bio_s_bio) BIO_s_bio;
extern BIO_METHOD *BIO_s_bio(void);
%rename(bio_s_mem) BIO_s_mem;
extern BIO_METHOD *BIO_s_mem(void);
%rename(bio_s_socket) BIO_s_socket;
extern BIO_METHOD *BIO_s_socket(void);
%rename(bio_f_ssl) BIO_f_ssl;
extern BIO_METHOD *BIO_f_ssl(void);
%rename(bio_f_buffer) BIO_f_buffer;
extern BIO_METHOD *BIO_f_buffer(void);
%rename(bio_f_cipher) BIO_f_cipher;
extern BIO_METHOD *BIO_f_cipher(void);

%rename(bio_new) BIO_new;
extern BIO *BIO_new(BIO_METHOD *);
%rename(bio_new_socket) BIO_new_socket;
extern BIO *BIO_new_socket(int, int);
%rename(bio_new_fd) BIO_new_fd;
extern BIO *BIO_new_fd(int, int);
%rename(bio_new_fp) BIO_new_fp;
extern BIO *BIO_new_fp(FILE *, int);
%rename(bio_new_file) BIO_new_file;
extern BIO *BIO_new_file(const char *, const char *);
%rename(bio_free) BIO_free;
extern int BIO_free(BIO *);
%rename(bio_free_all) BIO_free_all;
extern void BIO_free_all(BIO *);
%rename(bio_dup_chain) BIO_dup_chain;
extern BIO *BIO_dup_chain(BIO *);

%rename(bio_push) BIO_push;
extern BIO *BIO_push(BIO *, BIO *);
%rename(bio_pop) BIO_pop;
extern BIO *BIO_pop(BIO *);

%constant int bio_noclose             = BIO_NOCLOSE;
%constant int bio_close               = BIO_CLOSE;
%constant int BIO_FLAGS_READ          = 0x01;
%constant int BIO_FLAGS_WRITE         = 0x02;
%constant int BIO_FLAGS_IO_SPECIAL    = 0x04;
%constant int BIO_FLAGS_RWS = (BIO_FLAGS_READ|BIO_FLAGS_WRITE|BIO_FLAGS_IO_SPECIAL);
%constant int BIO_FLAGS_SHOULD_RETRY  = 0x08;
%constant int BIO_FLAGS_MEM_RDONLY    = 0x200;

%inline %{
static PyObject *_bio_err;

void bio_init(PyObject *bio_err) {
    Py_INCREF(bio_err);
    _bio_err = bio_err;
}

PyObject *bio_read(BIO *bio, int num) {
    PyObject *blob;
    void *buf;
    int r;

    if (!(buf = PyMem_Malloc(num))) {
        PyErr_SetString(PyExc_MemoryError, "bio_read");
        return NULL;
    }
    Py_BEGIN_ALLOW_THREADS
    r = BIO_read(bio, buf, num);
    Py_END_ALLOW_THREADS
    if (r < 0) {
        PyMem_Free(buf);
        if (ERR_peek_error()) {
            PyErr_SetString(_bio_err, ERR_reason_error_string(ERR_get_error()));
            return NULL;
        }
        Py_INCREF(Py_None);
        return Py_None;
    }
    blob = PyString_FromStringAndSize(buf, r);
    PyMem_Free(buf);
    return blob;
}

PyObject *bio_gets(BIO *bio, int num) {
    PyObject *blob;
    void *buf;
    int r;

    if (!(buf = PyMem_Malloc(num))) {
        PyErr_SetString(PyExc_MemoryError, "bio_gets");
        return NULL;
    }
    Py_BEGIN_ALLOW_THREADS
    r = BIO_gets(bio, buf, num);
    Py_END_ALLOW_THREADS
    if (r < 0) {
        PyMem_Free(buf);
        if (ERR_peek_error()) {
            PyErr_SetString(_bio_err, ERR_reason_error_string(ERR_get_error()));
            return NULL;
        }
        Py_INCREF(Py_None);
        return Py_None;
    }
    blob = PyString_FromStringAndSize(buf, r);
    PyMem_Free(buf);
    return blob;
}

int bio_write(BIO *bio, PyObject *from) {
    const void *fbuf;
    int flen, ret;

    if (m2_PyObject_AsReadBufferInt(from, &fbuf, &flen) == -1)
        return -1;

    Py_BEGIN_ALLOW_THREADS
    ret = BIO_write(bio, fbuf, flen);
    Py_END_ALLOW_THREADS
    if (ret < 0) {
        if (ERR_peek_error()) {
            PyErr_SetString(_bio_err, ERR_reason_error_string(ERR_get_error()));
        }
    }
    return ret;
}

/* XXX Casting size_t to int. */
int bio_ctrl_pending(BIO *bio) {
    return (int)BIO_ctrl_pending(bio);
}

int bio_ctrl_wpending(BIO *bio) {
    return (int)BIO_ctrl_wpending(bio);
}

int bio_ctrl_get_write_guarantee(BIO *a) {
    return BIO_ctrl_get_write_guarantee(a);
}

int bio_reset(BIO *bio) {
    return (int)BIO_reset(bio);
}

int bio_flush(BIO *bio) {
    return (int)BIO_flush(bio);
}

int bio_seek(BIO *bio, int offset) {
    return (int)BIO_seek(bio, offset);
}

void bio_set_flags(BIO *bio, int flags) {
    BIO_set_flags(bio, flags);
}

int bio_get_flags(BIO *bio) {
    return BIO_get_flags(bio);
}

PyObject *bio_set_cipher(BIO *b, EVP_CIPHER *c, PyObject *key, PyObject *iv, int op) {
    const void *kbuf, *ibuf;
    Py_ssize_t klen, ilen;

    if ((PyObject_AsReadBuffer(key, &kbuf, &klen) == -1)
        || (PyObject_AsReadBuffer(iv, &ibuf, &ilen) == -1))
        return NULL;

    BIO_set_cipher(b, (const EVP_CIPHER *)c, 
        (unsigned char *)kbuf, (unsigned char *)ibuf, op);
    Py_INCREF(Py_None);
    return Py_None;
}

int bio_set_mem_eof_return(BIO *b, int v) {
    return (int)BIO_set_mem_eof_return(b, v);
}

int bio_get_fd(BIO *bio) {
    return BIO_get_fd(bio, NULL);
}

int bio_do_handshake(BIO *bio) {
    return BIO_do_handshake(bio);
}

/* macro */
int bio_make_bio_pair(BIO* b1, BIO* b2) {
    return BIO_make_bio_pair(b1, b2);
}

int bio_set_write_buf_size(BIO* b, size_t size) {
    return BIO_set_write_buf_size(b, size);
}

int bio_should_retry(BIO* a) {
    return BIO_should_retry(a);
}

int bio_should_read(BIO* a) {
    return BIO_should_read(a);
}

int bio_should_write(BIO* a) {
    return BIO_should_write(a);
}
%}

