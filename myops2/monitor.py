#!/usr/bin/env python 

import sys, os, signal, time, datetime
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

''' A thread that will check if new resources have been added
'''
def resources():
    print "==> Reteiving resources %s" % (datetime.datetime.now())
    db = db()
    ''' PLE nodes '''
    nodes = Query('Nodes').ple().execute()
    for node in nodes :
        db.update_resource(node)
    db.commit()
    db.close()

''' A thread that that will wekup with a timer and return the resources 
    that need to be monitored
'''
def monitor():
    pass

''' A thread that will check resource availability and information
'''
def agent(num, input, output):
    print 'Worker: %s' % num
    while True :
        
        node = input.get()
        
        resource = { 
            'hostname': node.hostname,
            'site_name': node.site,
            'status': 'up',
            'availability': 1
        }

        if not node.enabled:
            print "!ENABLED %s (%s)" % (resource['hostname'], resource['site_name'])
            resource['status'] = 'disabled'
            resource['availability'] = 0
        
        elif not node.is_running() :
            print "!RUN %s (%s)" % (resource['hostname'], resource['site_name'])
            resource['status'] = 'down'
            resource['availability'] = 0

        elif not node.is_accessible() :
            print "!ACC %s (%s)" % (resource['hostname'], resource['site_name'])
            resource['status'] = 'no access'
            resource['availability'] = 0
        
        #print "OK %s (%s)" % (resource['hostname'], resource['site_name'])
        
        #db.update(resource)
        
        ''' send OML stream '''
        oml.availability(resource['hostname'], resource['availability'])
        
        output.put(node)
    #input.task_done()
            
if __name__ == '__main__':
    signal.signal(signal.SIGINT, receive_signal)
    #signal.signal(signal.SIGUSR2, receive_signal)

    resources()
    exit
    
    ''' input queue '''
    input = Queue.Queue()
    ''' output queue '''
    output = Queue.Queue()
    
    
    
    ''' init Threads '''
    threads = []
    for y in range(10):
        t = threading.Thread(target=agent, args=(y, input, output))
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
    
        