/*
 * -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
 * vim: syntax=c sts=4 sw=4
 *
 * ENGINE functions from engine(3SSL).
 * 
 * Pavel Shramov
 * IMEC MSU
 */
%{
#include <openssl/engine.h>
#include <openssl/ui.h>
#include <stdio.h>
%}

%apply Pointer NONNULL { ENGINE * };
%apply Pointer NONNULL { const ENGINE * };
%apply Pointer NONNULL { const char * };

/*
 * Functions to load different engines
 */
%rename(engine_load_builtin_engines) ENGINE_load_builtin_engines;
extern void ENGINE_load_builtin_engines(void);

%rename(engine_load_dynamic) ENGINE_load_dynamic;
extern void ENGINE_load_dynamic(void);

%rename(engine_load_openssl) ENGINE_load_openssl;
extern void ENGINE_load_openssl(void);

%rename(engine_cleanup) ENGINE_cleanup;
extern void ENGINE_cleanup(void);

/*
 * Engine allocation functions
 */
%rename(engine_new) ENGINE_new;
extern ENGINE * ENGINE_new();

%rename(engine_by_id) ENGINE_by_id;
extern ENGINE * ENGINE_by_id(const char *);

%rename(engine_free) ENGINE_free;
extern int ENGINE_free(ENGINE *);

/*
 * Engine id/name functions
 */
%rename(engine_get_id) ENGINE_get_id;
extern const char * ENGINE_get_id(const ENGINE *);

%rename(engine_get_name) ENGINE_get_name;
extern const char * ENGINE_get_name(const ENGINE *);

/*
 * Engine control functions
 * Control argument may be NULL (e.g for LOAD command)
 */
%clear const char *;
%rename(engine_ctrl_cmd_string) ENGINE_ctrl_cmd_string;
extern int ENGINE_ctrl_cmd_string(ENGINE *e, const char *NONNULL, 
                const char *arg, int cmd_optional);

%apply Pointer NONNULL { const char * };

/*
 * UI methods. 
 * XXX: UI_OpenSSL method is static and UI_destroy_method is not needed.
 */
%rename(ui_openssl) UI_OpenSSL;
extern UI_METHOD * UI_OpenSSL();

/*
%rename(ui_destroy_method) UI_destroy_method;
extern void UI_destroy_method(UI_METHOD *ui_method);
 */

%clear const char *;
%inline %{

/*
 * Code from engine-pkcs11 1.4.0 in engine-pkcs11.c
 *

99  static char *get_pin(UI_METHOD * ui_method, void *callback_data, char *sc_pin,
100                      int maxlen)
101 {
102         UI *ui;
103         struct {
104                 const void *password;
105                 const char *prompt_info;
106         } *mycb = callback_data;
107 
108         if (mycb->password) {
109                 sc_pin = set_pin(mycb->password);
110                 return sc_pin;
111         }
 
 *
 * So callback_data need to be always provided and have fixed type.
 * UI method still may be NULL.
 *
 * Following functions allocate and free callback data structure with 
 * optional password set.
 */

typedef struct {
    char * password;
    char * prompt;
} _cbd_t;

void * engine_pkcs11_data_new(const char *pin) {
    _cbd_t * cb = (_cbd_t *) PyMem_Malloc(sizeof(_cbd_t));
    if (!cb) {
        PyErr_SetString(PyExc_MemoryError, "engine_pkcs11_data_new");
        return NULL;
    }
    cb->password = NULL;
    if (pin) {
        size_t size = strlen(pin);
        cb->password = (char *) PyMem_Malloc(size + 1);
        if (!cb->password) {
            PyErr_SetString(PyExc_MemoryError, "engine_pkcs11_data_new");
            PyMem_Free(cb);
            return NULL;
        }
        memcpy(cb->password, pin, size + 1);
    }
    cb->prompt = NULL;
    return cb;
}

void engine_pkcs11_data_free(void * vcb) {
    _cbd_t * cb = (_cbd_t *) vcb;
    if (!cb)
        return;
    if (cb->password)
        PyMem_Free(cb->password);
    PyMem_Free(cb);
}

%}
%apply Pointer NONNULL { const char * };

/*
 * Engine key/cert load functions.
 * See above notice about callback_data.
 */
%rename(engine_load_private_key) ENGINE_load_private_key;
extern EVP_PKEY *ENGINE_load_private_key(ENGINE *e, const char *key_id,
                    UI_METHOD *ui_method, void *callback_data);
%rename(engine_load_public_key) ENGINE_load_public_key;
extern EVP_PKEY *ENGINE_load_public_key(ENGINE *e, const char *key_id,
                    UI_METHOD *ui_method, void *callback_data);

/*
 * This function may be not implemented in engine.
 * pkcs11 engine has this control.
 */
%inline %{
static PyObject *_engine_err;

void engine_init(PyObject *engine_err) {
    Py_INCREF(engine_err);
    _engine_err = engine_err;
}

X509 * engine_load_certificate(ENGINE *e, const char * slot) {
    struct {
        const char * slot;
        X509 * cert;
    } cbd;
    cbd.slot = slot;
    cbd.cert = NULL;
    if (!ENGINE_ctrl_cmd(e, "LOAD_CERT_CTRL", 0, &cbd, NULL, 0)) {
        PyErr_SetString(_engine_err, "cannot load certificate");
        return NULL;
    }
    return cbd.cert;
}
%}

/* These flags are used to control combinations of algorithm (methods)
 * by bitwise "OR"ing. */
%constant int ENGINE_METHOD_RSA = 0x0001;
%constant int ENGINE_METHOD_DSA = 0x0002;
%constant int ENGINE_METHOD_DH = 0x0004;
%constant int ENGINE_METHOD_RAND = 0x0008;
%constant int ENGINE_METHOD_ECDH = 0x0010;
%constant int ENGINE_METHOD_ECDSA = 0x0020;
%constant int ENGINE_METHOD_CIPHERS = 0x0040;
%constant int ENGINE_METHOD_DIGESTS = 0x0080;
%constant int ENGINE_METHOD_STORE = 0x0100;
/* Obvious all-or-nothing cases. */
%constant int ENGINE_METHOD_ALL = 0xFFFF;
%constant int ENGINE_METHOD_NONE = 0x0000;

%rename(engine_set_default) ENGINE_set_default;
extern int ENGINE_set_default(ENGINE *e, unsigned int flags);

