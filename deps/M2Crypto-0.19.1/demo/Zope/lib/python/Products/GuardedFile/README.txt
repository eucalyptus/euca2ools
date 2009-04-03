GuardedFile

    A GuardedFile is a Zope File that is accessible *by proxy* only.

    When a GuardedFile is created, all acquired permissions are unset. 
    A proxy role is created in its container with the sole permission 
    "View".

    When the GuardedFile is deleted, its associated proxy role is also
    removed.

    In all other aspects a GuardedFile behaves exactly like a File.

    
    $Id: README.txt 299 2005-06-09 17:32:28Z heikki $
    $Revision: 1.2 $
