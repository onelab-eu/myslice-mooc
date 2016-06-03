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
import signal
import os
import errno

logger = logging.getLogger(__name__)

def handle_timeout(signum, frame):
    raise TimeoutError(os.strerror(errno.ETIME))

signal.signal(signal.SIGALRM, handle_timeout)

class TimeoutError(Exception):
    pass

def remote_worker(hostname, script):
    # timeout after 15 min
    signal.alarm(900)

    logger.info("Running job '%s' on %s" % (script, hostname))

    try:
        result = remote.script(hostname, script)
    except TimeoutError:
        logger.info("job '%s' timeout on %s" % (script, hostname))
        ret = {
            'jobstatus': 'error',
            'message': 'job timeout',
            'returnstatus': 1,
            'stdout': '',
            'stderr': ''
        }
    except Exception, msg:
        logger.info("job '%s' exception on %s ($s)" % (script, hostname, msg))
        ret = {
            'jobstatus': 'error',
            'message': msg,
            'returnstatus': 1,
            'stdout': '',
            'stderr': ''
        }
    else:
        logger.info("job '%s' completed on %s" % (script, hostname))
        try:
            r = json.loads(result)
        except Exception, msg:
            logger.error("JSON error: %s" % (msg,))
            ret = {
                'jobstatus': 'error',
                'message': 'job error',
                'returnstatus': 1,
                'stdout': '',
                'stderr': ''
            }
        else:
            ret = {
                'jobstatus': 'finished',
                'message': 'job completed',
                'returnstatus': r['returnstatus'],
                'stdout': r['stdout'],
                'stderr': r['stderr']
            }
    finally:
        signal.alarm(0)

    return ret


def process_job(num, input):
    """
    This worker will try to check for resource availability

    """

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

        logger.info("Job: %s" % (j,))

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
                'jobstatus': 'error',
                'message': 'node not reachable',
                'returnstatus': 1,
                'stdout': '',
                'stderr': result['message']
            }
            
        else :

            if j['command'] == 'ping':
                command = 'ping'

                remote_command = '%s.py %s %s' % (command, j['parameters']['arg'], j['parameters']['dst'])

                try:
                    ret = remote_worker(j['node'], remote_command)
                except Exception, msg:
                    logger.error("EXEC error: %s" % (msg,))
                    upd = {
                        'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': "execution error %s" % (msg)
                    }
                    logger.error("execution error %s" % (msg))
                else:
                    upd = {
                        'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        'jobstatus': ret['jobstatus'],
                        'message': ret['message'],
                        'returnstatus': ret['returnstatus'],
                        'stdout': ret['stdout'],
                        'stderr': ret['stderr']
                    }
                    logger.info("Command executed, result: %s" % (upd))

            elif j['command'] == 'traceroute':
                command = 'traceroute'

                remote_command = '%s.py %s %s' % (command, j['parameters']['arg'], j['parameters']['dst'])

                try:
                    ret = remote_worker(j['node'], remote_command)
                except Exception, msg:
                    logger.error("EXEC error: %s" % (msg,))
                    upd = {
                        'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': "execution error %s" % (msg)
                    }
                    logger.error("execution error %s" % (msg))
                else:
                    upd = {
                        'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        'jobstatus': ret['jobstatus'],
                        'message': ret['message'],
                        'returnstatus': ret['returnstatus'],
                        'stdout': ret['stdout'],
                        'stderr': ret['stderr']
                    }
                    logger.info("Command executed, result: %s" % (upd))

            elif j['command'] == 'iperf':

                ##
                # setup second node
                result_dst = remote.setup(j['parameters']['dst'])

                if not result_dst['status']:

                    logger.error("%s : Failed SSH access (%s)" % (j['parameters']['dst'], result_dst['message']))
                    upd = {
                        'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': "Node %s not responding" % (j['parameters']['dst'])
                    }
                    logger.error("Node %s not responding" % (j['parameters']['dst']))

                else:

                    # server (thread)
                    remote_command_server = "iperf.py -s"
                    ts = threading.Thread(target=remote_worker, args=(j['node'], remote_command_server))
                    ts.start()

                    time.sleep(2)

                    # client
                    remote_command_client = "iperf.py -c %s %s" % (j['node'], j['parameters']['arg'])

                    try:
                        ret = remote_worker(j['parameters']['dst'], remote_command_client)
                    except Exception, msg:
                        upd = {
                            'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            'jobstatus': 'error',
                            'message': 'job error',
                            'returnstatus': 1,
                            'stdout': '',
                            'stderr': "execution error %s" % (msg)
                        }
                        logger.error("execution error %s" % (msg))
                    else:
                        upd = {
                            'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            'jobstatus': ret['jobstatus'],
                            'message': ret['message'],
                            'returnstatus': ret['returnstatus'],
                            'stdout': ret['stdout'],
                            'stderr': ret['stderr']
                        }
                        logger.info("Command executed, result: %s" % (upd))

            else :
                upd = {
                    'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'jobstatus': 'error',
                    'message': 'job error',
                    'returnstatus': 1,
                    'stdout': '',
                    'stderr': 'unknown command'
                }
                logger.error("Command %s not found" % (j['command']))


        r.table('jobs').get(job).update(upd).run(c)
