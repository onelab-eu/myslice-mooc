#!/usr/bin/env python 

import sys, os, signal, time
import sqlite3
import Queue
import threading
import db, oml

from planetlab.query import Query
# from planetlab.test import Service
# from planetlab.test import Packages
# from planetlab.test import Node

def receive_signal(signum, stack):
    print 'Received:', signum
    raise SystemExit('Exiting')
    
def worker(num, input, output):
    print 'Worker: %s' % num
    resource = {}
    while True :
        
        node = input.get()
        
        resource.hostname = node.hostname
        resource.site_name = node.site
        resource.status = 'up'
        resource.availability = 1

        if not node.enabled:
            print "!ENABLED %s (%s)" % (resource.hostname, resource.site_name)
            resource.status = 'disabled'
            resource.availability = 0
        
        elif not node.is_running() :
            print "!RUN %s (%s)" % (resource.hostname, resource.site_name)
            resource.status = 'down'
            resource.availability = 0

        elif not node.is_accessible() :
            print "!ACC %s (%s)" % (resource.hostname, resource.site_name)
            resource.status = 'no access'
            resource.availability = 0
        
        print "OK %s (%s)" % (resource.hostname, resource.site_name)
        
        #db.update(resource)
        
        ''' send OML stream '''
        oml.availability(resource.hostname, resource.availability)
        
        output.put(node)
    #input.task_done()
            
if __name__ == '__main__':
    signal.signal(signal.SIGINT, receive_signal)
    #signal.signal(signal.SIGUSR2, receive_signal)

    
    ''' input queue '''
    input = Queue.Queue()
    ''' output queue '''
    output = Queue.Queue()
    
    ''' initial queue '''
    nodes = Query('Nodes').ple().execute()
    for node in nodes :
        input.put(node)
    
    ''' init Threads '''
    threads = []
    for y in range(10):
        t = threading.Thread(target=worker, args=(y, input, output))
        t.daemon = True
        threads.append(t)
        t.start()
            
    ''' main Thread '''
    while True:
        ret = output.get()
        #print 'checked: %s' % (ret)
        input.put(ret)

    
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
    
        