'''
    MyOps2 - a new monitoring system for PlanetLab and other testbeds

    Workers to monitor the resources

    (c) 2014 - 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
'''
import logging

import lib.store as s
from planetlab.query import Query

def availability(input):
    """
    This worker will try to check for resource availability

    """
    logging.info("Agent %s starting" % num)

    while True:
        resource = input.get()

        node = Query('Nodes').hostname(resource).execute().first()

        s.update({
            "hostname": node.hostname,
            "bootstate": node.boot,
            "status": status
        })

    pass

def information(input):
    pass