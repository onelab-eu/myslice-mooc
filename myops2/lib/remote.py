'''
    MyOps2 - a new monitoring system for PlanetLab and other testbeds
    
    This module is used to retrieve system information on a node
    
    (c) 2014 - 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
    
'''

import paramiko
import json

env.skip_bad_hosts = True
env.connection_attempts = 1
env.timeout = 1
env.user = 'root'
env.abort_on_prompts = True
env.disable_known_hosts = True
#env.key_filename = '~/.ssh/planetlab_root_ssh_key.rsa'
#env.key_filename = '/etc/planetlab/planetlab_root_ssh_key.rsa'

REMOTE_DIR="/root/.myops2"
REMOTE_SCRIPTS=['cpu','disk','load','mem','net','procs','system','uptime','users']

def connect():

def setup():
    transport = paramiko.Transport((myhost, 22))
    transport.connect(username = myusername, key_filename='')

    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        sftp.chdir(remote_path)  # Test if remote_path exists
    except IOError:
        sftp.mkdir(remote_path)  # Create remote_path
        sftp.chdir(remote_path)
    sftp.put(local_path, '.')    # At this point, you are in remote_path in either case
    sftp.close()


@task
def information():
    ''' prepare remote environment and execute the scripts '''
    result = []

    if not files.exists(REMOTE_DIR):
        run("mkdir %s" % REMOTE_DIR)

    for script in REMOTE_SCRIPTS:
        #if not files.exists("%s/%s.py" % (REMOTE_DIR, script)):
        put("scripts/%s.py" % script, REMOTE_DIR, mode=0755)

        result.append({ script : json.loads(run("%s/%s.py" % (REMOTE_DIR, script))) })

    return result

@task
def pingtask():
    with settings(warn_only=True):
        res = run("id")
        print "status:",res.status


def rexecute(host):

    result = []
    with settings(hide('running', 'commands', 'stdout', 'stderr')):
        result = execute(information, hosts=host)

    for h in result:
        print json.dumps(result[h])
        print '===='

def ping(host):
    execute(pingtask,hosts=host)


if __name__ == '__main__':
    #rexecute(['sybaris.ipv6.lip6.fr'])
    ping(['sybaris.ipv6.lip6.fr'])