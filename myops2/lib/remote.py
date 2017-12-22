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
import os
from scp import SCPClient
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
remote_tmp_dir = "/home/upmc_kvermeulen/tmp"
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

    try:
        sftp = paramiko.SFTPClient.from_transport(transport)
    except Exception as e:
        logger.error('SFTP error: {}'.format(e))

    try:
        sftp.chdir(remote_dir)  # Test if remote_path exists
    except IOError:
        sftp.mkdir(remote_dir)  # Create remote_path
        sftp.chdir(remote_dir)

    for file_name in glob.glob(local_dir + '/*.*'):
        local_file = os.path.join(local_dir, file_name)
        remote_file = remote_dir + '/' + os.path.basename(file_name)

        # check if remote file exists
        try:
            if sftp.stat(remote_file):
                local_file_data = open(local_file, "rb").read()
                remote_file_data = sftp.open(remote_file).read()
                md1 = hashlib.md5(local_file_data).digest()
                md2 = hashlib.md5(remote_file_data).digest()
                if md1 == md2:
                    pass
                    # print "UNCHANGED:", os.path.basename(file_name)
                else:
                    # print "MODIFIED:", os.path.basename(file_name)
                    sftp.put(local_file, remote_file)
        except:
            # print "NEW: ", os.path.basename(file_name)
            sftp.put(local_file, remote_file)
            sftp.chmod(remote_file, 0755)
    sftp.close()


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
            time.sleep(0.1)
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

def execute(num, hostname, command, destinations, semaphore_map):

    result = ''
    output = ''

    ssh = connect(hostname, semaphore_map)

    scp = SCPClient(ssh.get_transport())

    destinations_tmp_file = "destinations"+ str(num)
    # Write the destinations into a file and copy it
    with open(destinations_tmp_file, "w") as destinations_file:
        for destination in destinations:
            destinations_file.write(destination + "\n")


    try:
        pkey = paramiko.RSAKey.from_private_key_file(rsa_private_key)
    except Exception as e:
        #print 'Failed loading' % (rsa_private_key, e)
        logger.error('Failed loading key')

    try:
        transport = paramiko.Transport((hostname, 22))
    except SSHException as e:
        # Transport setup error
        logger.error('Failed SSH connection (%s)' % (e))
    except Exception as e:
        logger.error('Transport error (%s)' % (e))

    try:
        transport.start_client()
    except SSHException as e:
        # if negotiation fails (and no event was passed in)
        logger.error('Failed SSH negotiation (%s)' % (e))

    try:
        transport.auth_publickey(username, pkey)
    except BadAuthenticationType as e:
        # if public-key authentication isn't allowed by the server for this user (and no event was passed in)
        logger.error('Failed public-key authentication (%s)' % (e))
    except AuthenticationException as e:
        # if the authentication failed (and no event was passed in)
        logger.error('Failed authentication (%s)' % (e))
    except SSHException as e:
        # if there was a network error
        logger.error('Network error (%s)' % (e))


    try:
        sftp = paramiko.SFTPClient.from_transport(transport)
    except Exception as e:
        logger.error('SFTP error: {}'.format(e))

    try:
        sftp.chdir(remote_tmp_dir)  # Test if remote_path exists
    except IOError:
        sftp.mkdir(remote_tmp_dir)  # Create remote_path
        sftp.chdir(remote_tmp_dir)

    try:
        sftp.put(destinations_tmp_file, remote_tmp_dir + "/"+ destinations_tmp_file)
    except Exception as e:
        logger.error("SFTP error (%s)" % (e))

    sftp.close()
    # Copy that file on the node
    # scp_destinations_command = "scp -oStrictHostKeyChecking=no "+ destinations_tmp_file + " upmc_kvermeulen@"+ hostname +":/tmp/"
    # os.system(scp_destinations_command)
    # scp.put(destinations_tmp_file, remote_path='/tmp/')
    #
    # scp.put("../scripts/paris-traceroute.py" , remote_path='/home/upmc_kvermeulen/.myops2')

    # scp_paris_traceroute_py_command = "scp -oStrictHostKeyChecking=no ../scripts/paris-traceroute.py " + " upmc_kvermeulen@"+ hostname +":/home/upmc_kvermeulen/.myops2/"
    # os.system(scp_paris_traceroute_py_command)
    # Send the command (non-blocking)
    logger.info("executing %s", (command,))
    try:
	    stdin, stdout, stderr = ssh.exec_command(command + " " + str(num))
    except SSHException as e:
        print e
	pass
    else:
	
    # Wait for the command to terminate
    # while not stdout.channel.exit_status_ready():
    #     # Only print data if there is data to read in the channel
    #     if stdout.channel.recv_ready():
    #         rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
    #         if len(rl) > 0:
    #             # Print data from stdout
    #             result += stdout.channel.recv(1024)

    	output = stdout.read()
        error = stderr.read()

    ssh.close()

    return output

def script(num, hostname, script, destinations, semaphore_map):
    '''
    Executes a script on the remote node.
    Scripts will return a json formatted string with result and information
    '''
    result = execute(num, hostname, remote_dir + "/" + script, destinations, semaphore_map)

    return result

if __name__ == '__main__':
    node = 'ple41.planet-lab.eu'
    setup(node)
    #r = script(node, 'networks.sh')
    #print r
