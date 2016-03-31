#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import platform
import json
import sys
import subprocess
import threading
import Queue

def run_command_with_timeout(cmd, timeout_sec=30):
    """Execute `cmd` in a subprocess and enforce timeout `timeout_sec` seconds.
    Return subprocess exit code on natural completion of the subprocess.
    Raise an exception if timeout expires before subprocess completes."""
    q = Queue.Queue()
    def wraps(f, *args):
        if args is None:
            q.put(f())
        else:
            q.put(f(args))

    proc = subprocess.Popen(
                cmd,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
                )
    proc_thread = threading.Thread(target=wraps, args = (proc.communicate, ))
    proc_thread.start()
    proc_thread.join(timeout_sec)
    if proc_thread.is_alive():
        try:
            proc.kill()
        except OSError, e:
            return proc.returncode
        #raise TimeoutError('Process #%d killed after %f seconds' % (proc.pid, timeout_sec))
    
    out, err = q.get()
    return proc.returncode, out, err

def run_command(cmd):
    proc = subprocess.Popen(
                cmd,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
                )
    out, err = proc.communicate()
    return proc.returncode, out, err

if __name__ == '__main__':

    # find the iperf package
    is_iperf = run_command(['which', 'iperf'])

    if not is_iperf[1]:

        if platform.dist()[1] > '22':
            commands = ['dnf', 'install', 'iperf']
        else:
            commands = ['yum', 'install', 'iperf']

        installation = run_command(commands)

        if not installation[1]:
            print json.dumps({
                'returnstatus': installation[0],
                'stdout': installation[1],
                'stderr': installation[2]
                })
            sys.exit(1)

    aguments = sys.argv

    # check if is server
    running_type = aguments[1]
    if running_type == '-s':
        iperf = run_command_with_timeout(['iperf'] + aguments[1:])
    else:
        iperf = run_command(['iperf'] + aguments[1:])
    print(iperf)
    print json.dumps({
        'returnstatus': iperf[0],
        'stdout': iperf[1],
        'stderr': iperf[2]
    })