#!/usr/bin/env python 

'''
    MyOps2 - a new monitoring system for PlanetLab and other testbeds
    
    (c) 2014 - 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
'''

import sys
import os
import signal
import time
import datetime
import logging
import threading

sys.path.append(os.path.realpath(os.path.dirname(__file__) + '/..'))

from lib.queue import OrderedSetQueue
#import lib.oml

from lib.worker import resources

try:
    import lib.store as s
except ImportError:
    logging.error("RethinkDB required")
    exit(1)

try:
    from planetlab.query import Query
except ImportError:
    logging.error("PlanetLab lib required")
    exit(1)


def receive_signal(signum, stack):
    print 'Received:', signum
    raise SystemExit('Exiting')




#
# def agent(num, input):
#     """
#     A thread that will check resource availability and information
#     """
#     logging.info("Agent %s starting" % num)
#
#     while True:
#         resource = input.get()
#
#         node = Query('Nodes').hostname(resource).execute().first()
#
#         if not node.enabled:
#             print "+=> (%s) %s is not enabled" % (node.boot, node.hostname)
#             availability = 0
#             status = "disabled"
#
#         elif not node.is_running():
#             print "+=> (%s) %s is not running" % (node.boot, node.hostname)
#             availability = 0
#             status = "down"
#         else:
#             # if not r:
#             #     print "+=> (%s) %s is not accessible" % (node.boot, node.hostname)
#             #     availability = 0
#             #     status = "no access"
#             # else :
#             #     print "+=> (%s) %s is ok" % (node.boot, node.hostname)
#             availability = 1
#             status = "up"
#                 #updates info about the node (testing)
#                 # d.info_resource(node.hostname, {
#                 #     #'ipv4' : node.ip(4),
#                 #     'ipv6' : node.ip(6),
#                 # })
#
#         s.update({
#             "hostname": node.hostname,
#             "bootstate": node.boot,
#             "status": status
#         })
#         ''' send OML stream '''
#         # oml.availability(node.hostname, availability)

            
if __name__ == '__main__':
    signal.signal(signal.SIGINT, receive_signal)
    signal.signal(signal.SIGTERM, receive_signal)

    ''' setup storage '''
    s.setup()

    ''' input queue '''
    input = OrderedSetQueue()

    ''' resources thread '''
    print "Starting resources thread"
    t = threading.Thread(target=resources.sync)
    t.daemon = True
    t.start()

    # agent threads
    # threads = []
    # for y in range(20):
    #     t = threading.Thread(target=agent, args=(y, input))
    #     t.daemon = True
    #     threads.append(t)
    #     t.start()

    ## main thread, periodically put resources to monitor
    ## in the input queue

    t.join()