import socket
import select
import os
import glob
import hashlib
import logging
import threading
import time
import re

import paramiko
from paramiko.ssh_exception import BadAuthenticationType, BadHostKeyException, AuthenticationException, SSHException

#logging.basicConfig(level=logging.DEBUG,
#                   format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
#                  datefmt="%Y-%m-%d %H:%M:%S")

logger = logging.getLogger(__name__)

# PlanetLab Lib is required
from planetlab import config

# static atm
#username = 'root'
username = config.get('remote','ssh_user')
#rsa_private_key = "/root/mooc/rest-api/key/planetlab_root_ssh_key.rsa"
rsa_private_key = config.get('remote','ssh_root_key')
logger.info(rsa_private_key)
remote_dir = "/home/upmc_kvermeulen/.myops2"
local_dir = os.path.realpath(os.path.dirname(__file__) + '/../scripts')


def setup(hostname, semaphore_map):

    result = { "status" : False, "message" : None }
    logger.info("connecting to %s", (hostname,))

    try:
        pkey = paramiko.RSAKey.from_private_key_file(rsa_private_key)
    except Exception as e:
        #print 'Failed loading' % (rsa_private_key, e)
        result["message"] = 'Failed loading key'
        logger.error('Failed loading key')
        return result

    try:
        transport = paramiko.Transport((hostname, 22))
    except SSHException as e:
        # Transport setup error
        result['message'] = 'Failed SSH connection (%s)' % (e)
        logger.error('Failed SSH connection (%s)' % (e))
        return result
    except Exception as e:
        result['message'] = 'Transport error (%s)' % (e)
        logger.error('Transport error (%s)' % (e))
        return result

    try:
        transport.start_client()
    except SSHException as e:
        # if negotiation fails (and no event was passed in)
        result['message'] = 'Failed SSH negotiation (%s)' % (e)
        logger.error('Failed SSH negotiation (%s)' % (e))
        return result

    try:
        transport.auth_publickey(username, pkey)
    except BadAuthenticationType as e:
        # if public-key authentication isn't allowed by the server for this user (and no event was passed in)
        result['message'] = 'Failed public-key authentication (%s)' % (e)
        logger.error('Failed public-key authentication (%s)' % (e))
        return result
    except AuthenticationException as e:
        # if the authentication failed (and no event was passed in)
        result['message'] = 'Failed authentication (%s)' % (e)
        logger.error('Failed authentication (%s)' % (e))
        return result
    except SSHException as e:
        # if there was a network error
        result['message'] = 'Network error (%s)' % (e)
        logger.error('Network error (%s)' % (e))
        return result

    #Testing the presence of TCPDUMP
    try:
        semaphore = semaphore_map[hostname]
        with semaphore:
            time.sleep(1)
            s = paramiko.SSHClient()
            #s.load_system_host_keys()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(hostname=hostname, username=username, key_filename=rsa_private_key)

            command = 'which tcpdump'
            (stdin, stdout, stderr) = s.exec_command(command)
            logger.info('********************************')
            logger.info('Executing "which tcpdump" ...')
            logger.info('********************************\n')

            if stdout.readlines() == []:
                logger.error("TCPDUMP is not present")
            else:
                logger.info("TCPDUMP found")

        #Testing the presence of WGET (web client)

            command = 'which wget'
            (stdin, stdout, stderr) = s.exec_command(command)
            logger.info('********************************')
            logger.info('Executing "which wget" ...')
            logger.info('********************************\n')

            if stdout.readlines() == []:
                logger.error("WGET is not present")
            else:
                logger.info("WGET found")

        #Testing the presence of CURL (web client)

            command = 'which curl'
            (stdin, stdout, stderr) = s.exec_command(command)
            logger.info('********************************')
            logger.info('Executing "which curl" ...')
            logger.info('********************************\n')

            if stdout.readlines() == []:
                logger.error("CURL is not present")
            else:
                logger.info("CURL found")

        #Testing the presence of APACHE (web server)

            command = 'ps aux | grep apache'
            (stdin, stdout, stderr) = s.exec_command(command)
            logger.info('********************************')
            logger.info('Executing "ps aux | grep apache" ...')
            logger.info('********************************\n')

            stdout_grep = stdout.readline()

            if stdout_grep.find("/usr/sbin/apache2") != -1:
                logger.info("Server web (APACHE) is running")
            else:
                logger.info("Server web (APACHE) is not running")

            s.close()
    except SSHException as e:
        result['message'] = 'Network error (%s)' % (e)
        logger.error('Network error (%s)' %(e))
        return result

    # try:
    #     sftp = paramiko.SFTPClient.from_transport(transport)
    # except Exception as e:
    #     logger.error('SFTP error: {}'.format(e))
    #     result['message'] = 'SFTP error (%s)' % (e)
    #     return result
    #
    # # try:
    # #     sftp.chdir(remote_dir)  # Test if remote_path exists
    # # except IOError:
    # #     sftp.mkdir(remote_dir)  # Create remote_path
    # #     sftp.chdir(remote_dir)
    # #
    # # for file_name in glob.glob(local_dir + '/*.*'):
    # #     local_file = os.path.join(local_dir, file_name)
    # #     remote_file = remote_dir + '/' + os.path.basename(file_name)
    # #
    # #     # check if remote file exists
    # #     try:
    # #         if sftp.stat(remote_file):
    # #             local_file_data = open(local_file, "rb").read()
    # #             remote_file_data = sftp.open(remote_file).read()
    # #             md1 = hashlib.md5(local_file_data).digest()
    # #             md2 = hashlib.md5(remote_file_data).digest()
    # #             if md1 == md2:
    # #                 pass
    # #                 #print "UNCHANGED:", os.path.basename(file_name)
    # #             else:
    # #                 #print "MODIFIED:", os.path.basename(file_name)
    # #                 sftp.put(local_file, remote_file)
    # #     except:
    # #         #print "NEW: ", os.path.basename(file_name)
    # #         sftp.put(local_file, remote_file)
    # #         sftp.chmod(remote_file, 0755)
    # sftp.close()

    result['status'] = True
    result['message'] = 'Setup complete'
    logger.info('Setup complete')
    return result

def connect(hostname, semaphore_map):
    '''
    Try to connect to remote host
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    logger.info("connecting to %s lock address : %d", hostname,id(semaphore_map[hostname]))
    try:
        semaphore = semaphore_map[hostname]
        with semaphore:
            time.sleep(0.25)
            ssh.connect(hostname=hostname, username=username, key_filename=rsa_private_key)
    except BadHostKeyException as e:
        logger.error(e)
    except AuthenticationException as e:
        logger.error(e)
    except SSHException as e:
        logger.error(e)
    except socket.error as e:
        logger.error(e)
    except IOError as e:
        logger.error(e)

    return ssh

def execute(hostname, command, semaphore_map):

    result = ''

    ssh = connect(hostname, semaphore_map)

    # Send the command (non-blocking)
    logger.info("executing %s", (command,))
    stdin, stdout, stderr = ssh.exec_command(command)

    # Wait for the command to terminate
    # while not stdout.channel.exit_status_ready():
    #     # Only print data if there is data to read in the channel
    #     if stdout.channel.recv_ready():
    #         rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
    #         if len(rl) > 0:
    #             # Print data from stdout
    #             result += stdout.channel.recv(1024)

    output = stdout.read()

    ssh.close()

    return output

def script(hostname, script, semaphore_map):
    '''
    Executes a script on the remote node.
    Scripts will return a json formatted string with result and information
    '''
    result = execute(hostname, remote_dir + "/" + script, semaphore_map)

    return result

if __name__ == '__main__':
    node = 'ple41.planet-lab.eu'
    setup(node)
    #r = script(node, 'networks.sh')
    #print r
