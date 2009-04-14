"""GuardedFile.GuardedFile

Copyright (c) 2000-2003 Ng Pheng Siong. All rights reserved.
This software is released under the ZPL. Usual disclaimers apply."""

__version__ = '1.3'

from AccessControl import getSecurityManager
from Globals import HTMLFile, MessageDialog
from OFS.Image import File, cookId

manage_addForm = HTMLFile('add', globals(),Kind='GuardedFile',kind='GuardedFile')
def manage_addGuardedFile(self, id, file, title='', precondition='', content_type='', REQUEST=None):
    """
    Add a new GuardedFile object.

    Creates a new GuardedFile object 'id' with the content of 'file'.
    """
    # Object creation stuff, cribbed from OFS.Image.manage_addFile().
    id, title = cookId(id, title, file)
    self = self.this()
    self._setObject(id, GuardedFile(id, title, '', content_type, precondition))
    obj = self._getOb(id)
    obj.manage_upload(file)

    # Unset permission acquisition.
    obj.manage_acquiredPermissions()

    # Create a proxy role and set a specific permission for it.
    proxy_role = "proxy_for_%s" % id
    self._addRole(proxy_role)
    obj.manage_role(proxy_role, ['View'])
    uname = getSecurityManager().getUser().getUserName()
    self.manage_addLocalRoles(uname, (proxy_role,), REQUEST)

    # Feedback.
    if REQUEST: return MessageDialog(
        title  ='Success!',
        message='GuardedFile "%s" has been created.' % id,
        action ='manage_main')
        

class GuardedFile(File):
    """A File object accessible by proxy only."""
    meta_type = "GuardedFile"

    def manage_beforeDelete(self, item, container):
        """Delete self's proxy role."""
        role = "proxy_for_%s" % self.__name__
        container._delRoles([role], None)
        self.manage_delLocalRoles(self.users_with_local_role(role))
 

