#!/usr/bin/env python 

import sys, os, signal, time
import sqlite3
import Queue
import threading

from planetlab.query import Query
# from planetlab.test import Service
# from planetlab.test import Packages
# from planetlab.test import Node

def receive_signal(signum, stack):
    print 'Received:', signum
    raise SystemExit('Exiting')
    
def worker(num, input, output):
    print 'Worker: %s' % num
    while True :
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        
        status = 'up'
        
        node = input.get()

        if not node.enabled:
            print "!ENABLED %s (%s)" % (node, node.site)
            status = 'disabled'
        
        elif not node.is_running() :
            print "!RUN %s (%s)" % (node, node.site)
            status = 'down'

        elif not node.is_accessible() :
            print "!ACC %s (%s)" % (node, node.site)
            status = 'no access'
        
        print "OK %s (%s)" % (node, node.site)
        
        c.execute("SELECT hostname FROM monitor WHERE hostname='%s'" % (node.hostname))
        if c.fetchone() :
            c.execute("UPDATE monitor SET status='%s' WHERE hostname='%s'" % (status, node.hostname))
        else :
            c.execute("INSERT INTO monitor (hostname,site,status) VALUES ('%s','%s','%s')" % (node.hostname,node.site.name,status))
        
        conn.commit()
        conn.close()
        output.put(node)
    #input.task_done()
            
if __name__ == '__main__':
    signal.signal(signal.SIGINT, receive_signal)
    #signal.signal(signal.SIGUSR2, receive_signal)

    ''' create sqlite table '''  
#     conn = sqlite3.connect('nodes.db')
#     c = conn.cursor()
#     c.execute('''CREATE TABLE monitor (
#         hostname text,
#         site text,
#         ipv4 text,
#         ipv6 text,
#         distro text,
#         kernel text,
#         cores integer,
#         cpu text,
#         ram text,
#         disk text,
#         status text,
#         checked integer)''')
    
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
    
        