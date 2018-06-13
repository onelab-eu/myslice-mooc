#!/usr/bin/env python

from Queue import Queue
import json
import sys
import subprocess
import datetime
from graph_tool.all import *
import os

def execute(item, output_queue, file_name):
    MDALite = subprocess.Popen(
        ["sudo", "/root/MDAPROTOTYPE/MDALite.py"] + item,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = MDALite.communicate()
    # Will create a file name with a space at the beginning. item's fault?
    # The XML file will be create at /root
    with open("/root/" + " " + file_name, "r") as graph_file:
        g = graph_file.read()

    output_queue.put((MDALite.returncode, g, err, item[len(item) - 1]))

    os.remove("/root/" + " " + file_name)


if __name__ == '__main__':

    output_queue = Queue()
    arguments = sys.argv
    hostname = arguments[1:]

    num = arguments[len(arguments) - 1]
    destinations_tmp_file = "/home/upmc_kvermeulen/tmp/destinations" + str(num)


    with open(destinations_tmp_file) as destinations:
        for destination in destinations:
            destination = destination.strip()
            file_name = destination + ".xml"
            args = arguments[1:len(arguments) - 1]
            # adding the output file name (e.g: 2.17.140.1.xml)
            args[3] = args[3] + " " + file_name
            args.append(destination)
            execute(args, output_queue, file_name)

    results = []
    while not output_queue.empty():
        result = output_queue.get()
        results.append({
            'returnstatus': result[0],
            'stdout': result[1],
            'stderr': result[2],
            'destination': result[3]
        })

    print json.dumps(results)


