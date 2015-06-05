#!/usr/bin/env python

'''
    MyOps2 - a new monitoring system for PlanetLab and other testbeds

    This app will launch the workers needed to setup the WEB interface,
    REST API and Websockets API

    (c) 2014 - 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
'''

import sys
import os
import logging

from tornado import web, ioloop

#sys.path.append(os.path.realpath(os.path.dirname(__file__) + '/..'))
#print os.path.realpath(os.path.dirname(__file__) + '/..')

from myops2.web import site
from myops2.protocol import rest, websocket

if __name__ == '__main__':

    print "Starting web thread"

    app = web.Application([
        (r'/', site.Index),
        (r'/static/(.*)', web.StaticFileHandler, {'path': site.static}),

    ], template_path=site.templates)

    app.listen(8111)

    api = web.Application([
        (r'/api', rest.Api),
    ])

    api.listen(8112)

    socket = web.Application([
        (r'/ws', websocket.Api)
    ])

    socket.listen(9001)

    try :
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        ioloop.IOLoop.instance().stop()
    except Exception as e:
        print e
        exit(1)

    # t = threading.Thread(target=server)
    # t.daemon = True
    # t.start()

    # agent threads
    # threads = []
    # for y in range(20):
    #     t = threading.Thread(target=agent, args=(y, input))
    #     t.daemon = True
    #     threads.append(t)
    #     t.start()

    ## main thread, periodically put resources to monitor
    ## in the input queue

    # t.join()