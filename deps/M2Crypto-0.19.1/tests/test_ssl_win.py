#!/usr/bin/env python

"""Unit tests for M2Crypto.SSL. 

Win32 version - requires Mark Hammond's Win32 extensions and openssl.exe 
on your PATH.

Copyright (c) 2000-2001 Ng Pheng Siong. All rights reserved."""

import os, os.path, string, time, unittest
import win32process

from M2Crypto import Rand, SSL
import test_ssl

def find_openssl():
    plist = os.environ['PATH'].split(';')
    for p in plist:
        try:
            dir = os.listdir(p)
            if 'openssl.exe' in dir:
                return os.path.join(p, 'openssl.exe')
        except WindowsError:
            pass
    return None


srv_host = 'localhost'
srv_port = 64000

class SSLWinClientTestCase(test_ssl.SSLClientTestCase):

    startupinfo = win32process.STARTUPINFO()
    openssl = find_openssl()

    def start_server(self, args):
        # openssl must be started in the tests directory for it
        # to find the .pem files
        os.chdir('tests')        
        try:
            hproc, hthread, pid, tid = win32process.CreateProcess(self.openssl,
                string.join(args), None, None, 0, win32process.DETACHED_PROCESS, 
                None, None, self.startupinfo)
        finally:
            os.chdir('..')            
        time.sleep(0.3)
        return hproc

    def stop_server(self, hproc):
        win32process.TerminateProcess(hproc, 0)


def suite():
    return unittest.makeSuite(SSLWinClientTestCase)

def zap_servers():
    pass


if __name__ == '__main__':
    try:
        if find_openssl() is not None:
            Rand.load_file('randpool.dat', -1) 
            unittest.TextTestRunner().run(suite())
            Rand.save_file('randpool.dat')
    finally:
        zap_servers()


