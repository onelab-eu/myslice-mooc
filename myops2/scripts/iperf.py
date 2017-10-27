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

def run_command_with_timeout(cmd, timeout_sec=20):
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
            return proc.returncode, 'fail to terminate the subprocess', 'os err'
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
    iperf_executable = 'iperf3'
    # find the iperf package
    is_iperf = run_command(['which', iperf_executable])

    if not is_iperf[1]:
        
        if platform.architecture()[0] == '64bit':
            commands = ['rpm', '-ivh', 'https://iperf.fr/download/fedora/iperf3-3.0.11-2.fc23.x86_64.rpm']
        else:
            commands = ['rpm', '-ivh', 'https://iperf.fr/download/fedora/iperf3-3.0.11-2.fc23.i686.rpm']
        
        install_code, out, err = run_command(commands)

        if err: 
            install_code, out, err = run_command(['yum', 'install', iperf_executable])

        if err:
            print json.dumps({
                'returnstatus': install_code,
                'stdout': out,
                'stderr': err
            })

    is_iperf = run_command(['which', iperf_executable])
    
    agruments = sys.argv
    running_type = agruments[1]
    
    if running_type == '-s':
        iperf = run_command_with_timeout([iperf_executable] + agruments[1:])
    elif running_type == '-c':
        #print('runnning client')
        iperf = run_command([iperf_executable] + agruments[1:])

    print json.dumps({
        'returnstatus': iperf[0],
        'stdout': iperf[1],
        'stderr': iperf[2]
    })