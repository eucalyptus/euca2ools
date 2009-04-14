/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/* Copyright (c) 1999-2004 Ng Pheng Siong. All rights reserved.  */
/*
** Portions created by Open Source Applications Foundation (OSAF) are
** Copyright (C) 2004 OSAF. All Rights Reserved.
*/
/* $Id: _asn1.i 522 2007-05-08 22:21:51Z heikki $ */

%{
#include <openssl/asn1.h>
%}

%apply Pointer NONNULL { BIO * };
%apply Pointer NONNULL { ASN1_OBJECT * };
%apply Pointer NONNULL { ASN1_STRING * };
%apply Pointer NONNULL { ASN1_INTEGER * };
%apply Pointer NONNULL { ASN1_UTCTIME * };

%rename(asn1_object_new) ASN1_OBJECT_new;
extern ASN1_OBJECT *ASN1_OBJECT_new( void );
%rename(asn1_object_create) ASN1_OBJECT_create;
extern ASN1_OBJECT *ASN1_OBJECT_create( int, unsigned char *, int, const char *, const char *);
%rename(asn1_object_free) ASN1_OBJECT_free;
extern void ASN1_OBJECT_free( ASN1_OBJECT *);
%rename(i2d_asn1_object) i2d_ASN1_OBJECT;
extern int i2d_ASN1_OBJECT( ASN1_OBJECT *, unsigned char **);
%rename(c2i_asn1_object) c2i_ASN1_OBJECT;
extern ASN1_OBJECT *c2i_ASN1_OBJECT( ASN1_OBJECT **, CONST098 unsigned char **, long);
%rename(d2i_asn1_object) d2i_ASN1_OBJECT;
extern ASN1_OBJECT *d2i_ASN1_OBJECT( ASN1_OBJECT **, CONST098 unsigned char **, long);

%rename(asn1_bit_string_new) ASN1_BIT_STRING_new;
extern ASN1_BIT_STRING *ASN1_BIT_STRING_new( void );

%rename(asn1_string_new) ASN1_STRING_new;
extern ASN1_STRING *ASN1_STRING_new( void );
%rename(asn1_string_free) ASN1_STRING_free;
extern void ASN1_STRING_free( ASN1_STRING *);

%typemap(in) (const void *, int) { 
    if (PyString_Check($input)) {
        Py_ssize_t len;

        $1 = PyString_AsString($input); 
        len = PyString_Size($input);
        if (len > INT_MAX) {
            PyErr_SetString(PyExc_ValueError, "object too large");
            return NULL;
        }
        $2 = len;
    } else {
        PyErr_SetString(PyExc_TypeError, "expected string");
        return NULL;
    }
}

%rename(asn1_string_set) ASN1_STRING_set;
extern int ASN1_STRING_set( ASN1_STRING *, const void *, int);

%typemap(in) (const void *, int);

%rename(asn1_string_print) ASN1_STRING_print;
extern int ASN1_STRING_print(BIO *, ASN1_STRING *);
%rename(asn1_string_print_ex) ASN1_STRING_print_ex;
extern int ASN1_STRING_print_ex(BIO *, ASN1_STRING *, unsigned long);

%rename(asn1_utctime_new) ASN1_UTCTIME_new;
extern ASN1_UTCTIME *ASN1_UTCTIME_new( void );
%rename(asn1_utctime_free) ASN1_UTCTIME_free;
extern void ASN1_UTCTIME_free(ASN1_UTCTIME *);
%rename(asn1_utctime_check) ASN1_UTCTIME_check;
extern int ASN1_UTCTIME_check(ASN1_UTCTIME *);
%rename(asn1_utctime_set) ASN1_UTCTIME_set;
extern ASN1_UTCTIME *ASN1_UTCTIME_set(ASN1_UTCTIME *, long);
%rename(asn1_utctime_set_string) ASN1_UTCTIME_set_string;
extern int ASN1_UTCTIME_set_string(ASN1_UTCTIME *, CONST098 char *);
%rename(asn1_utctime_print) ASN1_UTCTIME_print;
extern int ASN1_UTCTIME_print(BIO *, ASN1_UTCTIME *);

%rename(asn1_integer_new) ASN1_INTEGER_new;
extern ASN1_INTEGER *ASN1_INTEGER_new( void );
%rename(asn1_integer_free) ASN1_INTEGER_free;
extern void ASN1_INTEGER_free( ASN1_INTEGER *);
%rename(asn1_integer_get) ASN1_INTEGER_get;
extern long ASN1_INTEGER_get(ASN1_INTEGER *);
%rename(asn1_integer_set) ASN1_INTEGER_set;
extern int ASN1_INTEGER_set(ASN1_INTEGER *, long);
%rename(asn1_integer_cmp) ASN1_INTEGER_cmp;
extern int ASN1_INTEGER_cmp(ASN1_INTEGER *, ASN1_INTEGER *);

%constant int ASN1_STRFLGS_ESC_2253 = 1;
%constant int ASN1_STRFLGS_ESC_CTRL = 2;
%constant int ASN1_STRFLGS_ESC_MSB = 4;
%constant int ASN1_STRFLGS_ESC_QUOTE = 8;
%constant int ASN1_STRFLGS_UTF8_CONVERT = 0x10;
%constant int ASN1_STRFLGS_DUMP_UNKNOWN = 0x100;
%constant int ASN1_STRFLGS_DUMP_DER = 0x200;
%constant int ASN1_STRFLGS_RFC2253 = (ASN1_STRFLGS_ESC_2253 | \
                ASN1_STRFLGS_ESC_CTRL | \
                ASN1_STRFLGS_ESC_MSB | \
                ASN1_STRFLGS_UTF8_CONVERT | \
                ASN1_STRFLGS_DUMP_UNKNOWN | \
                ASN1_STRFLGS_DUMP_DER);

%inline %{
/* ASN1_UTCTIME_set_string () is a macro */
int asn1_utctime_type_check(ASN1_UTCTIME *ASN1_UTCTIME) {
    return 1;
}

%}
