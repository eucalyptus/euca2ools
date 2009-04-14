/* Copyright (c) 1999 Ng Pheng Siong. All rights reserved. */
/* $Id: _lib.h 593 2007-10-12 21:46:34Z heikki $ */

#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
#endif

typedef struct _blob {
	unsigned char *data;
	int len;
} Blob;

Blob *blob_new(int len, const char *errmsg);
Blob *blob_copy(Blob *from, const char *errmsg);
void blob_free(Blob *blob);

static int m2_PyObject_AsReadBufferInt(PyObject *obj, const void **buffer,
                                       int *buffer_len);
static int m2_PyString_AsStringAndSizeInt(PyObject *obj, char **s, int *len);

void gen_callback(int p, int n, void *arg);
int passphrase_callback(char *buf, int num, int v, void *userdata);

void lib_init(void);

