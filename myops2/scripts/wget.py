#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import json
import sys
import subprocess


if __name__ == '__main__':

    arguments = sys.argv
    hostname = arguments[1:]

    # http://cdimage.ubuntu.com/ubuntu/releases/16.04/release/ubuntu-16.04-server-s390x.template
    pcap_process = subprocess.Popen(['tcpdump', '-s', '0', 'port', 'ftp', 'or', 'http', '-i', 'eth0', '-w', 'mypcap.pcap'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    wget = subprocess.Popen(
                ["wget"] + arguments[1:],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
                )
    out, err = wget.communicate()

    pcap_process.terminate()
    pcap_out, pcap_err = pcap_process.communicate()

    # If wget is successful, return a siplified message
    # drop the progression of downloading percentage
    if wget.returncode == 0:
        out = '\n'.join([err.split('\n\n')[0],err.split('\n\n')[2]])
        err = ''

    # If pcap is successful, send the file to a URL
    # return this url to the user
    #if pcap_process.returncode == 0:
    #    # Where to scp the pcap?

    print json.dumps({
        'returnstatus': wget.returncode,
        'stdout': out,
        'stderr': err
    })
