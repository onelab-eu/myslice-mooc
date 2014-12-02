#!/usr/bin/env python 

import sys, os, signal, time, datetime
import logging
import threading
from queue import OrderedSetQueue
from db import db
import oml

from planetlab.query import Query
# from planetlab.test import Service
# from planetlab.test import Packages
# from planetlab.test import Node


def receive_signal(signum, stack):
    print 'Received:', signum
    raise SystemExit('Exiting')

''' A thread that will check if new resources have been added
'''
def resources():
    while True :
        logging.info("==> Reteiving resources %s" % (datetime.datetime.now()))
        
        d = db()
        ''' PLE nodes '''
        nodes = Query('Nodes').ple().execute()
        for node in nodes :
            d.update_resource(node)
        d.commit()
        d.close()
        time.sleep(86400)

''' A thread that will check resource availability and information
'''
def agent(num, input):
    
    logging.info("Agent %s starting" % (num))
    
    d = db()
    
    while True :
        resource = input.get()
        
        node = Query('Nodes').hostname(resource).execute().first()
        
        if not node.enabled:
            print "+=> %s is not enabled" % (node.hostname)
            availability = 0
            status = "disabled"
        
        elif not node.is_running() :
            print "+=> %s is not running" % (node.hostname)
            availability = 0
            status = "down"

        elif not node.is_accessible() :
            print "+=> %s is not accessible" % (node.hostname)
            availability = 0
            status = "no access"
        else :
            print "+=> %s is ok" % (node.hostname)
            availability = 1
            status = "up"
        
        ''' send OML stream '''
        #oml.availability(node.hostname, availability)
        
        d.status_resource(node.hostname, status)
        d.commit()
            
if __name__ == '__main__':
    signal.signal(signal.SIGINT, receive_signal)
    #signal.signal(signal.SIGUSR2, receive_signal)
    
    ''' input queue '''
    input = OrderedSetQueue()
    
    ''' resources thread '''
    logging.info("Starting resources thread")
    t = threading.Thread(target=resources)
    t.daemon = True
    t.start()
        
    ''' agent threads '''
    threads = []
    for y in range(10):
        t = threading.Thread(target=agent, args=(y, input))
        t.daemon = True
        threads.append(t)
        t.start()
            
    ''' The main thread will return the resources 
        that need to be monitored
    '''
    logging.info("Main Thread")
    while True:
        d = db()
        resources = d.select_resources()
        if resources :
            for resource in resources :
                input.put(resource['hostname'])
        time.sleep(60)
        