"""An FTP/TLS server built on Medusa's ftp_server. 

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

# Python
import socket, string, sys, time

# Medusa
from counter import counter
import asynchat, asyncore, ftp_server, logger

# M2Crypto
from M2Crypto import SSL

VERSION_STRING='0.09'

class ftp_tls_channel(ftp_server.ftp_channel):
    
    """FTP/TLS server channel for Medusa."""

    def __init__(self, server, ssl_ctx, conn, addr):
        """Initialise the channel."""
        self.ssl_ctx = ssl_ctx
        self.server = server
        self.current_mode = 'a'
        self.addr = addr
        asynchat.async_chat.__init__(self, conn)
        self.set_terminator('\r\n')
        self.client_addr = (addr[0], 21)
        self.client_dc = None
        self.in_buffer = ''
        self.closing = 0
        self.passive_acceptor = None
        self.passive_connection = None
        self.filesystem = None
        self.authorized = 0
        self._ssl_accepting = 0
        self._ssl_accepted = 0
        self._pbsz = None
        self._prot = None
        resp = '220 %s M2Crypto (Medusa) FTP/TLS server v%s ready.'
        self.respond(resp % (self.server.hostname, VERSION_STRING))

    def writable(self):
        return self._ssl_accepting or self._ssl_accepted

    def handle_read(self):
        """Handle a read event."""
        if self._ssl_accepting:
            self._ssl_accepted = self.socket.accept_ssl()
            if self._ssl_accepted:
                self._ssl_accepting = 0
        else:
            try:
                ftp_server.ftp_channel.handle_read(self) 
            except SSL.SSLError, what:
                if str(what) == 'unexpected eof':
                    self.close()
                else:
                    raise

    def handle_write(self):
        """Handle a write event."""
        if self._ssl_accepting:
            self._ssl_accepted = self.socket.accept_ssl()
            if self._ssl_accepted:
                self._ssl_accepting = 0
        else:
            try:
                ftp_server.ftp_channel.handle_write(self) 
            except SSL.SSLError, what:
                if str(what) == 'unexpected eof':
                    self.close()
                else:
                    raise

    def send(self, data):
        """Send data over SSL."""
        try:
            result = self.socket.send(data)
            if result <= 0:
                return 0
            else:
                return result
        except SSL.SSLError, what:
            self.close()
            self.log_info('send: closing channel %s %s' % (repr(self), what))
            return 0

    def recv(self, buffer_size):
        """Receive data over SSL."""
        try:
            result = self.socket.recv(buffer_size)
            if not result:
                return ''
            else:
                return result
        except SSL.SSLError, what:
            self.close()
            self.log_info('recv: closing channel %s %s' % (repr(self), what))
            return ''

    def found_terminator(self):
        """Dispatch the FTP command."""
        line = self.in_buffer
        if not len(line):
            return

        sp = string.find(line, ' ')
        if sp != -1:
            line = [line[:sp], line[sp+1:]]
        else:
            line = [line]

        command = string.lower(line[0])
        if string.find(command, 'stor') != -1:
            while command and command[0] not in string.letters:
                command = command[1:]
        
        func_name = 'cmd_%s' % command
        if command != 'pass':
            self.log('<== %s' % repr(self.in_buffer)[1:-1])
        else:
            self.log('<== %s' % line[0]+' <password>')

        self.in_buffer = ''
        if not hasattr(self, func_name):
            self.command_not_understood(line[0])
            return 
    
        func = getattr(self, func_name)
        if not self.check_command_authorization(command):
            self.command_not_authorized(command)
        else:
            try:
                result = apply(func, (line,))
            except:
                self.server.total_exceptions.increment()
                (file, func, line), t, v, tbinfo = asyncore.compact_traceback()
                if self.client_dc:
                    try:
                        self.client_dc_close()
                    except:
                        pass
                resp = '451 Server error: %s, %s: file %s line: %s'
                self.respond(resp % (t, v, file, line))

    def make_xmit_channel(self):
        """Create a connection for sending data."""
        pa = self.passive_acceptor
        if pa:
            if pa.ready:
                conn, addr = pa.ready
                if self._prot:
                    cdc = tls_xmit_channel(self, conn, self.ssl_ctx, addr)
                else:
                    cdc = ftp_server.xmit_channel(self, addr)
                    cdc.set_socket(conn)
                cdc.connected = 1
                self.passive_acceptor.close()
                self.passive_acceptor = None
            else:
                if self._prot:
                    cdc = tls_xmit_channel(self, None, self.ssl_ctx, None)
                else:
                    cdc = ftp_server.xmit_channel(self)
        else:
            if self._prot:
                cdc = tls_xmit_channel(self, None, self.ssl_ctx, self.client_addr)
            else:
                cdc = ftp_server.xmit_channel(self, self.client_addr)
            cdc.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.bind_local_minus_one:
                cdc.bind(('', self.server.port - 1))
            try:
                cdc.connect(self.client_addr)
            except socket.error, what:
                self.respond('425 Cannot build data connection')
        self.client_dc = cdc

    def make_recv_channel(self, fd):
        """Create a connection for receiving data."""
        pa = self.passive_acceptor
        if pa:
            if pa.ready:
                conn, addr = pa.ready
                if self._prot:
                    cdc = tls_recv_channel(self, conn, self.ssl_ctx, addr, fd)
                else:
                    cdc = ftp_server.recv_channel(self, addr, fd)
                cdc.set_socket(conn)
                cdc.connected = 1
                self.passive_acceptor.close()
                self.passive_acceptor = None
            else:
                if self._prot:
                    cdc = tls_recv_channel(self, None, self.ssl_ctx, None, fd)
                else:
                    cdc = ftp_server.recv_channel(self, None, fd)
        else:
            if self._prot:
                cdc = tls_recv_channel(self, None, self.ssl_ctx, self._prot, self.client_addr, fd)
            else:
                cdc = ftp_server.recv_channel(self, self.client_addr, fd)
            cdc.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                cdc.connect(self.client_addr)
            except socket.error, what:
                self.respond('425 Cannot build data connection')
        self.client_dc = cdc

    def cmd_auth(self, line):
        """Prepare for TLS operation."""
        # XXX Handle variations.
        if line[1] != 'TLS':
            self.command_not_understood (string.join(line))
        else:
            self.respond('234 AUTH TLS successful')
            self._ssl_accepting = 1
            self.socket = SSL.Connection(self.ssl_ctx, self.socket)    
            self.socket.setup_addr(self.addr)
            self.socket.setup_ssl()
            self.socket.set_accept_state()
            self._ssl_accepted = self.socket.accept_ssl()
            if self._ssl_accepted:
                self._ssl_accepting = 0

    def cmd_pbsz(self, line):
        """Negotiate size of buffer for secure data transfer. For
        FTP/TLS the only valid value for the parameter is '0'; any 
        other value is accepted but ignored."""
        if not (self._ssl_accepting or self._ssl_accepted):
            return self.respond('503 AUTH TLS must be issued prior to PBSZ')
        self._pbsz = 1
        self.respond('200 PBSZ=0 successful.')

    def cmd_prot(self, line):
        """Negotiate the security level of the data connection.""" 
        if self._pbsz is None:
            return self.respond('503 PBSZ must be issued prior to PROT')
        if line[1] == 'C':
            self.respond('200 Protection set to Clear')
            self._pbsz = None
            self._prot = None
        elif line[1] == 'P': 
            self.respond('200 Protection set to Private')
            self._prot = 1
        elif line[1] in ('S', 'E'):
            self.respond('536 PROT %s unsupported' % line[1])
        else:
            self.respond('504 PROT %s unsupported' % line[1])
            

class ftp_tls_server(ftp_server.ftp_server):

    """FTP/TLS server for Medusa."""

    SERVER_IDENT = 'M2Crypto FTP/TLS Server (v%s)' % VERSION_STRING

    ftp_channel_class = ftp_tls_channel

    def __init__(self, authz, ssl_ctx, host=None, ip='', port=21, resolver=None, log_obj=None):
        """Initialise the server."""
        self.ssl_ctx = ssl_ctx
        self.ip = ip
        self.port = port
        self.authorizer = authz

        if host is None:
            self.hostname = socket.gethostname()
        else:
            self.hostname = host

        self.total_sessions = counter()
        self.closed_sessions = counter()
        self.total_files_out = counter()
        self.total_files_in = counter()
        self.total_bytes_out = counter()
        self.total_bytes_in = counter()
        self.total_exceptions = counter()

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((self.ip, self.port))
        self.listen(5)

        if log_obj is None:
            log_obj = sys.stdout

        if resolver:
            self.logger = logger.resolving_logger(resolver, log_obj)
        else:
            self.logger = logger.unresolving_logger(logger.file_logger(sys.stdout))

        l = 'M2Crypto (Medusa) FTP/TLS server started at %s\n\tAuthz: %s\n\tHostname: %s\n\tPort: %d'
        self.log_info(l % (time.ctime(time.time()), repr(self.authorizer), self.hostname, self.port))

    def handle_accept(self):
        """Accept a socket and dispatch a channel to handle it."""
        conn, addr = self.accept()
        self.total_sessions.increment()
        self.log_info('Connection from %s:%d' % addr)
        self.ftp_channel_class(self, self.ssl_ctx, conn, addr)


class nbio_ftp_tls_actor:

    """TLS protocol negotiation mixin for FTP/TLS."""

    def tls_init(self, sock, ssl_ctx, client_addr):
        """Perform TLS protocol negotiation."""
        self.ssl_ctx = ssl_ctx
        self.client_addr = client_addr
        self._ssl_handshaking = 1
        self._ssl_handshake_ok = 0
        if sock:
            self.socket = SSL.Connection(self.ssl_ctx, sock)
            self.socket.setup_addr(self.client_addr)
            self.socket.setup_ssl()
            self._ssl_handshake_ok = self.socket.accept_ssl()
            if self._ssl_handshake_ok:
                self._ssl_handshaking = 0
            self.add_channel()
        # else the client hasn't connected yet; when that happens,
        # handle_connect() will be triggered.

    def tls_neg_ok(self):
        """Return status of TLS protocol negotiation."""
        if self._ssl_handshaking:
            self._ssl_handshake_ok = self.socket.accept_ssl()
            if self._ssl_handshake_ok:
                self._ssl_handshaking = 0
        return self._ssl_handshake_ok

    def handle_connect(self):
        """Handle a data connection that occurs after this instance came 
        into being. When this handler is triggered, self.socket has been 
        created and refers to the underlying connected socket."""
        self.socket = SSL.Connection(self.ssl_ctx, self.socket)
        self.socket.setup_addr(self.client_addr)
        self.socket.setup_ssl()
        self._ssl_handshake_ok = self.socket.accept_ssl()
        if self._ssl_handshake_ok:
            self._ssl_handshaking = 0
        self.add_channel()

    def send(self, data):
        """Send data over SSL."""
        try:
            result = self.socket.send(data)
            if result <= 0:
                return 0
            else:
                return result
        except SSL.SSLError, what:
            self.close()
            self.log_info('send: closing channel %s %s' % (repr(self), what))
            return 0

    def recv(self, buffer_size):
        """Receive data over SSL."""
        try:
            result = self.socket.recv(buffer_size)
            if not result:
                return ''
            else:
                return result
        except SSL.SSLError, what:
            self.close()
            self.log_info('recv: closing channel %s %s' % (repr(self), what))
            return ''
 

class tls_xmit_channel(nbio_ftp_tls_actor, ftp_server.xmit_channel):

    """TLS driver for a send-only data connection."""

    def __init__(self, channel, conn, ssl_ctx, client_addr=None):
        """Initialise the driver."""
        ftp_server.xmit_channel.__init__(self, channel, client_addr)
        self.tls_init(conn, ssl_ctx, client_addr)

    def readable(self):
        """This channel is readable iff TLS negotiation is in progress.
        (Which implies a connected channel, of course.)"""
        if not self.connected:
            return 0
        else:
            return self._ssl_handshaking

    def writable(self):
        """This channel is writable iff TLS negotiation is in progress
        or the application has data to send."""
        if self._ssl_handshaking:
            return 1
        else:
            return ftp_server.xmit_channel.writable(self)

    def handle_read(self):
        """Handle a read event: either continue with TLS negotiation
        or let the application handle this event."""
        if self.tls_neg_ok():
            ftp_server.xmit_channel.handle_read(self) 

    def handle_write(self):
        """Handle a write event: either continue with TLS negotiation
        or let the application handle this event."""
        if self.tls_neg_ok():
            ftp_server.xmit_channel.handle_write(self) 


class tls_recv_channel(nbio_ftp_tls_actor, ftp_server.recv_channel):
    
    """TLS driver for a receive-only data connection."""

    def __init__(self, channel, conn, ssl_ctx, client_addr, fd):
        """Initialise the driver."""
        ftp_server.recv_channel.__init__(self, channel, client_addr, fd)
        self.tls_init(conn, ssl_ctx, client_addr)

    def writable(self):
        """This channel is writable iff TLS negotiation is in progress."""
        return self._ssl_handshaking

    def handle_read(self):
        """Handle a read event: either continue with TLS negotiation
        or let the application handle this event."""
        if self.tls_neg_ok():
            ftp_server.recv_channel.handle_read(self) 

    def handle_write(self):
        """Handle a write event: either continue with TLS negotiation
        or let the application handle this event."""
        if self.tls_neg_ok():
            ftp_server.recv_channel.handle_write(self) 


