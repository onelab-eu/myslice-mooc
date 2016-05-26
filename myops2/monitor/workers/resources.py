'''
    MyOps2 - a new monitoring system for PlanetLab and other testbeds

    Workers to manage the list of resources

    (c) 2014 - 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
'''

import time
import datetime
import random
import logging

from planetlab.query import Query

import myops2.lib.store as s

'''
    resource discovery thread: will retrieve resources from a remote end
        - it will not remove old resources that were deleted/removed from remote end db
'''
def sync():

    logger = logging.getLogger(__name__)

    ''' DB connection '''
    c = s.connect()

    """
    This worker retrieves the list of resources from the testbed(s)
    """
    while True:
        logger.info("Retreiving resources %s", datetime.datetime.now())

        ''' PLE nodes '''
        try:
            nodes = Query('Nodes').ple().execute()
            for node in nodes:
                s.resource(c,
                    {
                        "testbed": "ple",
                        "hostname": node.hostname
                    }
                )

        except Exception as e:
            logger.exception("Service does not seem to be available")
            exit(1)
        exit(0)
        #time.sleep(86400)

'''
    resource prepare thread: will prepare resources to be checked
    - will double check if the resource still exists on the remote end, if not it will
      delete it (or disable) locally.
    - will retrieve resources last checked X seconds ago and put them in the input queue
'''
def queue(input):

    while True:
        resources = s.select()
        if resources:
            for resource in resources:
                input.put(resource['hostname'])
        time.sleep(30)