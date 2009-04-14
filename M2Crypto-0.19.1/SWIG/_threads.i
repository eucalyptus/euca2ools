/* Copyright (c) 1999 Ng Pheng Siong. All rights reserved. */
/* $Id: _threads.i 555 2007-06-14 06:29:31Z heikki $ */

%{
#include <pythread.h>
#include <openssl/crypto.h>

#ifdef THREADING
static PyThread_type_lock lock_cs[CRYPTO_NUM_LOCKS];
static long lock_count[CRYPTO_NUM_LOCKS];
static int thread_mode = 0;
#endif

void threading_locking_callback(int mode, int type, const char *file, int line) {
#ifdef THREADING
        if (mode & CRYPTO_LOCK) {
                PyThread_acquire_lock(lock_cs[type], 0);
                lock_count[type]++;
        } else {
                PyThread_release_lock(lock_cs[type]);
                lock_count[type]--;
        }
#endif
}

unsigned long threading_id_callback(void) {
#ifdef THREADING
    return (unsigned long)PyThread_get_thread_ident();
#else
    return (unsigned long)0;
#endif
}
%}

%inline %{
void threading_init(void) {
#ifdef THREADING
    int i;
    if (!thread_mode) {
        for (i=0; i<CRYPTO_NUM_LOCKS; i++) {
            lock_count[i]=0;
            lock_cs[i]=PyThread_allocate_lock();
        }
        CRYPTO_set_id_callback(threading_id_callback);
        CRYPTO_set_locking_callback(threading_locking_callback);
    }
    thread_mode = 1;
#endif
}

void threading_cleanup(void) {
#ifdef THREADING
    int i;
    if (thread_mode) {
        CRYPTO_set_locking_callback(NULL);
        for (i=0; i<CRYPTO_NUM_LOCKS; i++) {
            lock_count[i]=0;
            PyThread_release_lock(lock_cs[i]);
            PyThread_free_lock(lock_cs[i]);
        }
    }
    thread_mode = 0;
#endif
}
%}

