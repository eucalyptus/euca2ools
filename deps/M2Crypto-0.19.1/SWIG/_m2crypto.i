/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/* Copyright (c) 1999-2002 Ng Pheng Siong. All rights reserved.
 *
 * Portions created by Open Source Applications Foundation (OSAF) are
 * Copyright (C) 2004-2006 OSAF. All Rights Reserved.
 */

%module _m2crypto

%{
#include <openssl/err.h>
#include <openssl/rand.h>
#include <_lib.h>

#include "compile.h"

static PyObject *ssl_verify_cb_func;
static PyObject *ssl_info_cb_func;
static PyObject *ssl_set_tmp_dh_cb_func;
static PyObject *ssl_set_tmp_rsa_cb_func;
%}

%include <openssl/opensslv.h>
#if OPENSSL_VERSION_NUMBER >= 0x0090707fL
#define CONST const
#else
#define CONST
#endif

#if OPENSSL_VERSION_NUMBER >= 0x0090800fL
#define CONST098 const
#else
#define CONST098
#endif

%include constraints.i
%include _threads.i
%include _lib.i
%include _bio.i
%include _bn.i
%include _rand.i
%include _evp.i
%include _aes.i
%include _rc4.i
%include _dh.i
%include _rsa.i
%include _dsa.i
%include _ssl.i
%include _x509.i
%include _asn1.i
%include _pkcs7.i
%include _util.i
%include _ec.i
%include _engine.i
%include _objects.i

#ifdef SWIG_VERSION
%constant int encrypt = 1;
%constant int decrypt = 0;
#endif
  
