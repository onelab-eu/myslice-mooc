import os
import socket
import traceback
import paramiko

def execute(hostname, command=None):
    # setup logging
    paramiko.util.log_to_file('demo.log')
    
    username = 'root'
    if hostname.find('@') >= 0:
        username, hostname = hostname.split('@')
    
    port = 22
    if hostname.find(':') >= 0:
        hostname, portstr = hostname.split(':')
        port = int(portstr)
    
    if command is None:
        command="id"
    
    # try to connect
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))
    except Exception as e:
        return (False, str(e))
    
    try:
        transport = paramiko.Transport(sock)
        try:
            transport.start_client()
        except paramiko.SSHException as e:
            return (False, str(e))
            
    
#         try:
#             keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
#         except IOError:
#             try:
#                 keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
#             except IOError:
#                 print('*** Unable to open host keys file')
#                 keys = {}
    
        # check server's host key -- this is important.
        key = transport.get_remote_server_key()
#         if hostname not in keys:
#             print('*** WARNING: Unknown host key!')
#         elif key.get_name() not in keys[hostname]:
#             print('*** WARNING: Unknown host key!')
#         elif keys[hostname][key.get_name()] != key:
#             print('*** WARNING: Host key has changed!!!')
#             sys.exit(1)
#         else:
#             print('*** Host key OK.')
    
#         path = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
# 
#         try:
#             key = paramiko.RSAKey.from_private_key_file(path)
#         except paramiko.PasswordRequiredException:
#             password = getpass.getpass('RSA key password: ')
#             key = paramiko.RSAKey.from_private_key_file(path, password)
#         transport.auth_publickey(username, key)
        
        rootkey = paramiko.RSAKey.from_private_key_file('/etc/planetlab/planetlab_root_ssh_key.rsa')
        transport.auth_publickey(username, rootkey)
        
        debugkey = paramiko.RSAKey.from_private_key_file('/etc/planetlab/planetlab_debug_ssh_key.rsa')
        transport.auth_publickey(username, debugkey)
        
        if not transport.is_authenticated():
            transport.close()
            return (False, 'Authentication failed.')
    
        channel = transport.open_session()
        
        channel.exec_command(command)
        ret = channel.recv_exit_status()
        if ret == 0 :
            r = True
        else :
            r = False
        
        out = ""
        
        data = channel.recv(1024)
        while data:
          out += data
          data = channel.recv(1024)
        
        
        channel.close()
        transport.close()
        
        return (r, out.strip())
    
    except Exception as e:
        try:
            transport.close()
        except:
            pass
        return (False, '*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
    
    
