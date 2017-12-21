#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

from Queue import Queue
import json
import sys
import subprocess

def execute(item, output_queue):
    paris_traceroute = subprocess.Popen(
        ["sudo", "/usr/local/bin/paris-traceroute"] + item,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = paris_traceroute.communicate()
    output_queue.put((paris_traceroute.returncode, out, err, item[len(item) - 1]))


if __name__ == '__main__':

    output_queue = Queue()
    arguments = sys.argv
    hostname = arguments[1:]

    num = arguments[len(arguments) - 1]
    destinations_tmp_file = "/tmp/destinations" + str(num)

    with open(destinations_tmp_file) as destinations:
        for destination in destinations:
            args = arguments[1:len(arguments) - 1]
            args.append(destination.strip("\n"))
            execute(args, output_queue)

    results = []
    while not output_queue.empty():
        result = output_queue.get()
        results.append({
            'returnstatus': result[0],
            'stdout': result[1],
            'stderr': result[2],
            'destination' : result[3]
        })

    print json.dumps(results)