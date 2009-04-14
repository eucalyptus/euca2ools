/*
 * -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
 * vim: syntax=c sts=4 sw=4
 *
 * ASN1_OBJECT manipulation functions from OBJ_obj2txt(3SSL).
 * 
 * Pavel Shramov
 * IMEC MSU
 */
%{
#include <openssl/objects.h>
%}

%apply Pointer NONNULL { ASN1_OBJECT * };
%apply Pointer NONNULL { const char * };

%rename(obj_nid2obj) OBJ_nid2obj;
extern ASN1_OBJECT * OBJ_nid2obj(int n);
%rename(obj_nid2ln)  OBJ_nid2ln;
extern const char *  OBJ_nid2ln(int n);
%rename(obj_nid2sn)  OBJ_nid2sn;
extern const char *  OBJ_nid2sn(int n);

%rename(obj_obj2nid) OBJ_obj2nid;
extern int OBJ_obj2nid(const ASN1_OBJECT *o);

%rename(obj_ln2nid) OBJ_ln2nid;
extern int OBJ_ln2nid(const char *ln);
%rename(obj_sn2nid) OBJ_sn2nid;
extern int OBJ_sn2nid(const char *sn);

%rename(obj_txt2nid) OBJ_txt2nid;
extern int OBJ_txt2nid(const char *s);

%rename(obj_txt2obj) OBJ_txt2obj;
extern ASN1_OBJECT * OBJ_txt2obj(const char *s, int no_name);


%rename(_obj_obj2txt) OBJ_obj2txt;
extern int OBJ_obj2txt(char *, int, const ASN1_OBJECT *, int);


%inline %{
/*
    Following code is working but man page declare that it won't
    OBJ_obj2txt(3SSL). OpenSSL 0.9.8e
    BUGS
       OBJ_obj2txt() is awkward and messy to use: it doesn’t follow the
       convention of other OpenSSL functions where the buffer can be set
       to NULL to determine the amount of data that should be written.
       Instead buf must point to a valid buffer and buf_len should be set
       to a positive value. A buffer length of 80 should be more than
       enough to handle any OID encountered in practice.

    But code (crypto/objects/obj_dat.c near line 438) has only one place
    where buf is not checked (when object pointer is NULL)

446         if ((a == NULL) || (a->data == NULL)) {
447                 buf[0]='\0';
448                 return(0);
449         }

    Since NULL pointer is guarded by SWIG this condition may not occur.

    OBJ_obj2txt always prints \0 at the end. But return value
    is amount of "good" bytes written. So memory is allocated for
    len + 1 bytes but only len bytes are marshalled to python.
 */
PyObject *obj_obj2txt(const ASN1_OBJECT *obj, int no_name)
{
    int len;
    PyObject *ret;
    char *buf;

    len = OBJ_obj2txt(0, 0, obj, no_name);
    if (len < 0) {
        PyErr_SetString(PyExc_RuntimeError, ERR_reason_error_string(ERR_get_error()));
        return NULL;
    }

    buf = PyMem_Malloc(len + 1);
    len = OBJ_obj2txt(buf, len + 1, obj, no_name);
    ret = PyString_FromStringAndSize(buf, len);
    PyMem_Free(buf);

    return ret;
}
%}
