#!/usr/bin/env python

import os, popen2, time
from socket import *

def main0():
    cin, cout = popen2.popen2('openssl s_server')
    cout.write('Q\n')
    cout.flush()
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('', 4433))
    s.close()

def main():
    pid = os.fork()
    if pid:
        time.sleep(1)
        os.kill(pid, 1)
        os.waitpid(pid, 0)
    else:
        os.execvp('openssl', ('s_server',))

if __name__ == '__main__':
    main()

