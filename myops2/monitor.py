#!/usr/bin/env python 

import sys, os, signal, time, datetime
import sqlite3
import Queue
import threading
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
        print "==> Reteiving resources %s" % (datetime.datetime.now())
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
    
    d = db()
    
    while True :
        resource = input.get()
        availability = 1
        status = "up"
        
        if not node.enabled:
            print "+=> %s is not enabled" % (resource.hostname)
            availability = 0
            status = "disabled"
        
        elif not node.is_running() :
            print "+=> %s is not running" % (resource.hostname)
            availability = 0
            status = "down"

        elif not node.is_accessible() :
            print "+=> %s is not accessible" % (resource.hostname)
            availability = 0
            status = "no access"
        
        ''' send OML stream '''
        oml.availability(resource.hostname, availability)
        
        d.status_resource(resource.hostname, status)
        d.commit()
            
if __name__ == '__main__':
    signal.signal(signal.SIGINT, receive_signal)
    #signal.signal(signal.SIGUSR2, receive_signal)
    
    ''' input queue '''
    input = Queue.Queue()
    
    ''' resources thread '''
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
    while True:
        d = db()
        resources = d.select_resources()
        if resources :
            for resource in resources :
                input.put(resource)
        #print 'checked: %s' % (ret)
        #input.put(ret)
        time.sleep(900)

    
#     queue = Queue.Queue()
#     
#     ''' start threads '''
#     for i in range(10):
#         t = CheckNodes(queue)
#         t.setDaemon(True)
#         t.start()
    
    
#     nodes = Query('Nodes').ple().execute()
#     print nodes.count()
#     for node in nodes :
#         print node.hostname
    
        #if node.enabled:
            #pass
            #queue.put(site.nodes)

    #queue.join()
    
    #Node.results()
    #Service.results()
    #Packages.results()
    
        