'''
    MyOps2 - a new monitoring system for PlanetLab and other testbeds

    Workers to execute jobs remotely (MOOC)

    (c) 2014 - 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
'''

import logging
import time
import json
from datetime import datetime
import Queue

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

from myops2.settings import Config
import myops2.lib.remote as remote

import threading

def process_job(num, input):
    """
    This worker will try to check for resource availability

    """
    logger = logging.getLogger(__name__)

    logger.info("Agent %s starting" % num)

    try :
        c = r.connect(host=Config.rethinkdb["host"], port=Config.rethinkdb["port"], db=Config.rethinkdb['db'])
    except r.RqlDriverError :
        logger.error("Can't connect to RethinkDB")
        raise SystemExit("Can't connect to RethinkDB")

    while True:
        job = input.get()
        logger.info("Agent %s processing job %s" % (num, job))

        j = r.table('jobs').get(job).run(c)

        r.table('jobs').get(job).update({
            'started': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
            'jobstatus': 'running',
            'message': 'executing job'
        }).run(c)

        result = remote.setup(j['node'])
        if not result['status'] :
            logger.info("%s : Failed SSH access (%s)" % (j['node'], result['message']))
            upd = {
                'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                'jobstatus': 'finished',
                'message': 'node not reachable',
                'returnstatus': 1,
                'stdout': '',
                'stderr': result['message']
            }
            #TODO - put the below code in the right place
            '''
        # preventing second command execution
        black_list = ['&&', '&', ';', '||']
        if any(black in j['parameters']['arg'] for black in black_list):
            logger.info("Hacking argument detected : (%s)" % (j['parameters']['arg']))
            upd = {
                'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                'jobstatus': 'finished',
                'message': 'Hack argument detected : %s ' % j['parameters']['arg'],
                'returnstatus': 1,
                'stdout': '',
                'stderr': ''
            }
            '''
        else :
            logger.info("Running job on %s" % (j['node']))

            if j['command'] == 'ping':
                scripts = ' '.join(['ping.py', j['parameters']['arg'], j['parameters']['dst']])
                ret = json.loads(remote.script(j['node'], scripts))
                #ret = json.loads(remote.script(j['node'],  'ping.py' + ' ' + j['parameters']['arg'] + ' ' + j['parameters']['dst']))
            elif j['command'] == 'traceroute':
                ret = json.loads(remote.script(j['node'], 'traceroute.py' + ' ' + j['parameters']['arg'] + ' ' + j['parameters']['dst']))
            elif j['command'] == 'iperf':
                # server
                ret = []
                def func(q, *param):
                    q.put(remote.script(*param))
                
                q = Queue.Queue()
                ts = threading.Thread(target = func, args=(q, j['node'], 'iperf.py' + ' ' + '-s'))
                tc = threading.Thread(target = func, args=(q, j['parameters']['dst'], 'iperf.py' + ' ' + '-c' + ' ' + j['node']))
                ts.start()
                logger.info("Running job on %s" % (j['node']))
                #time.sleep(5)
                tc.start()
                logger.info("Running job on %s" % (j['parameters']['dst']))
                tc.join()
                ts.join()
                 
                for i in range(2):
                    ret += [q.get()]
                     
                print(ret)

                # server = remote.script(j['node'], 'iperf.py' + ' ' + '-s')
                # print(server)
                # #print(j['parameters']['dst'])
                # client = remote.script(j['parameters']['dst'], 'iperf.py' + ' ' + '-c' + ' ' + j['node'] + ' ' +j['parameters']['arg'])
                # print(client)
                # # client
                # #ret = json.loads(client)
                # logger.info("result is %s ..."% ret)
            else :
                ret = False

            if ret:
                upd = {
                    'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'jobstatus': 'finished',
                    'message': 'job completed',
                    'returnstatus': ret['returnstatus'],
                    'stdout': ret['stdout'],
                    'stderr': ret['stderr']
                }
                logger.info("Command executed on %s" % (j['node']))
            else:
                upd = {
                    'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'jobstatus': 'finished',
                    'message': 'job error',
                    'returnstatus': 1,
                    'stdout': '',
                    'stderr': 'unknown command'
                }
                logger.error("Command %s not found" % (j['command']))

        r.table('jobs').get(job).update(upd).run(c)