# !/usr/bin/python
import requests
import json
import sched, time
import sys, getopt
import threading
import random
import signal
import logging	
import rethinkdb as r
from datetime import datetime

#server url
db_host = "localhost"
db_name = "myops2"
db_port = 28015



def startSendRequestTask(body):
    #r = requests.post(serverUrl, json=body)
    r.raise_for_status()
    date = datetime.now(r.make_timezone('01:00'))

def start():
    conn = r.connect(db_host, db_port)
    # Read command line args
    myopts, args = getopt.getopt(sys.argv[1:], "i:o:")
    if len(sys.argv) < 2:
        print("Usage: <config_file>")
        exit(1)

    # Parse the config files and fill the tasks.
    with open(sys.argv[1]) as configFile:
        config = json.load(configFile)
        for measure in config:
            type = measure["type"]
            sources = measure["sources"]
            destinations = measure["destinations"]
            commands = measure["commands"]

            # Statically generate all JSON body we'll need to
            jsonBodies = []
            for source in sources:
                destinations_to_probe = []
                for destination in destinations:
                    if source != destination:
                        destinations_to_probe.append(destination)
                for experiment in commands:
                    command = experiment["command"]
                    #TODO implements filter logic
                    #filteredSrc = experiment["filterSrc"]
                    #filteredDst = experiment["filterDst"]
                    #####################################
                    body = {}
                    if command == "traceroute":
                        body = {
                                "node": source,
                                "type":"ple",
                                "command": command,
                                "parameters": {
                                "dst": destinations_to_probe,
                                "arg": "-n"
                                },
                                "jobstatus": "waiting",
                                "message": "waiting to be executed",
                                "created": r.expr(datetime.now(r.make_timezone('01:00'))),
                                "started": "",
                                "completed": "",
                                "returnstatus": "",
                                "stdout": "",
                                "stderr": ""
                                }
                    elif command == "paris-traceroute":
                        ts = time.time()

                        if type == "ple":
                            body = {
                                   "node": source,
                                   "type":"ple",
                                   "command": command,
                                   "parameters": {
                                   "dst": destinations_to_probe,
                                   "arg": "-amda -n -Fripe -t15"
                                   },
                                   "jobstatus": "waiting",
                                   "message": "waiting to be executed",
                                   "created": r.expr(datetime.now(r.make_timezone('01:00'))),
                                   "started": "",
                                   "completed": "",
                                   "returnstatus": "",
                                   "stdout": "",
                                   "stderr": ""
                                   }
                        elif type == "ripe":
                            body = {
                                   "node": str(source),
                                   "type":"ripe",
                                   "command": "traceroute",
                                   "parameters": {
                                   "dst": destinations_to_probe,
                                   "arg": "-n"
                                   },
                                   "jobstatus": "waiting",
                                   "message": "waiting to be executed",
                                   "created": r.expr(datetime.now(r.make_timezone('01:00'))),
                                   "started": "",
                                   "completed": "",
                                   "returnstatus": "",
                                   "stdout": "",
                                   "stderr": ""
                                   }

                    else:
                        raise Exception("Unknown command in your config_file")
                    #frequency = experiment["frequency"]
                    jsonBodies.append(body)



            # A good bound of the jobs we will have to launch is numberOfCommands*numberOfSrcs*numberOfDestinations
           # pool = ThreadPoolExecutor(len(commands) * len(sources) * len(destinations))
        while True:
            for body in jsonBodies:
                        r.db(db_name).table('jobs').insert(body).run(conn)
                        #startSendRequestTask(body["body"])
                        #r = requests.post(serverUrl, json=measure["body"])
                        #r.raise_for_status()
                        #time.sleep(0.05)
            time.sleep(int(sys.argv[2]))

# Format of the json file :
# frequencey is in seconds
# {
#     "sources": ["ple42.planet-lab.eu", "..."],
#     "destinations": ["google.com", "facebook.com"],
#     "commands": [{"command": "traceroute",
#                   "options": [],
#                   "filterSrc": [],
#                   "filterDst": [],
#                   "frequency": 300
#                   },
#                  {"command": "paris-traceroute",
#                   "options": [],
#                   "filterSrc": [],
#                   "filterDst": [],
#                   "frequency": 300
#                   }]
# }

def receive_signal(signum, stack):
    raise SystemExit('Exiting')

if __name__ == '__main__':

    signal.signal(signal.SIGINT, receive_signal)
    signal.signal(signal.SIGTERM, receive_signal)
    signal.signal(signal.SIGHUP, receive_signal)
    start()
 

