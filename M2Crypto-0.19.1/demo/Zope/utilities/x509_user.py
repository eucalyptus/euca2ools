#!/usr/bin/env python

"""
This is a very simple program to manage the access_x509 database. The 
overriding goal is program portability, hence its use of 'anydbm'.

Invoke it thusly:

    x509_user.py 
        -u <username> 
        [ -x <X.509 subject DN> ]
        [ -f <database> ] 

<username> is the Zope username; it must be present.

<X.509 subject DN> is the X.509 certificate's subject distinguished name
to associate with the user. If it is present, the association is created 
or updated. If it is absent, the association is removed.

<database> defaults to 'access_x509'.

(I told you this is a dumb program.)


To read the subject distinguished name from the certificate 'client.pem', 
invoke 'openssl' thusly:

    openssl x509 -subject -noout -in client.pem

This produces the output:

    subject=/C=SG/O=M2Crypto Client/CN=M2Crypto Client/Email=ngps@post1.com


Next, invoke this tool:

    x509_user.py -u superuser \\
        -f "/C=SG/O=M2Crypto Client/CN=M2Crypto Client/Email=ngps@post1.com"

This associates the user who owns client.pem to the Zope "superuser".


Copyright (c) 2000 Ng Pheng Siong. This program is released under the ZPL.
"""

import anydbm, getopt, sys

x509_db = 'access_x509'
username = subject_dn = None

argerr='Usage'

optlist, optarg=getopt.getopt(sys.argv[1:], 'f:u:x:')   # ;-)
for opt in optlist:
    if '-f' in opt:
        x509_db = opt[1]
    elif '-u' in opt:
        username = opt[1]
    elif '-x' in opt:
        subject_dn = opt[1]

if username is None:
    raise argerr, '\n' + __doc__

db = anydbm.open(x509_db, 'cw')
if subject_dn is None:
    # Remove the association...
    try:
        subject_dn = db[username]
        del db[subject_dn]
        del db[username]
    except:
        pass
else:
    # Create/update the association.
    db[subject_dn] = username
    db[username] = subject_dn
db.close()

