'''
    MyOps2 - a new monitoring system for PlanetLab and other testbeds

    Workers to manage the list of resources

    (c) 2014 - 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
'''
import logging
import time
import datetime

import lib.store as s
from planetlab.query import Query
import random

def sync():
    """
    This worker retrieves the list of resources from the testbed(s)
    """
    while True:
        print "Retreiving resources %s" % (datetime.datetime.now())

        ''' test '''
        while True:
            data = random.randint(1, 1000000)
            s.update({
                "test" : data
            })
            print data
            time.sleep(1)
        exit(0)
        ''' PLE nodes '''
        try:
            nodes = Query('Nodes').ple().execute()
            for node in nodes:
                site = node.site
                s.update({
                    "hostname": node.hostname,
                    "testbed": {
                        "name": "PlanetLab Europe",
                        "short": "PLE",
                        "facility": "onelab"
                    },
                    "site": {
                        "id": site.site_id,
                        "name" : site.name,
                        "short": site.abbreviated_name,
                        "login_base": site.login_base
                    }
                })

        except Exception as e:
            print "Service does not seem to be available"
            print e
            exit(1)
        exit(0)
        #time.sleep(86400)

def queue(input):
    """
    This worker is responsible of putting resources to monitor in the input queue
    input: the input queue

    """
    logging.info("Main Thread")
    while True:
        resources = s.select()
        if resources:
            for resource in resources:
                input.put(resource['hostname'])
        time.sleep(30)