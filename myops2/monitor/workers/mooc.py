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

class TimeoutError(Exception):
    pass

def handle_timeout(signum, frame):
    raise TimeoutError(os.strerror(errno.ETIME))

signal.signal(signal.SIGALRM, handle_timeout)

def remote_worker(*param):
    # timout after 15 min
    signal.alarm(900)

    try:
        result = remote.script(*param)
    finally:
        signal.alarm(0)

    return result



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

        logger.info("Job: %s" % (j,))

        r.table('jobs').get(job).update({
            'started': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
            'jobstatus': 'running',
            'message': 'executing job'
        }).run(c)

        error_msg = 'job error'

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

            if j['command'] == 'ping':
                command = 'ping'

                remote_command = '%s.py %s %s' % (command, j['parameters']['arg'], j['parameters']['dst'])

                logger.info("Running job (%s) on %s" % (remote_command, j['node']))

                try:
                    ret = json.loads(remote_worker(j['node'], remote_command))
                except TimeoutError:
                    ret = False
                    error_msg = 'job timeout'

            elif j['command'] == 'traceroute':
                command = 'traceroute'

                remote_command = '%s.py %s %s' % (command, j['parameters']['arg'], j['parameters']['dst'])

                logger.info("Running job (%s) on %s" % (remote_command, j['node']))

                try:
                    ret = json.loads(remote_worker(j['node'], remote_command))
                except TimeoutError:
                    ret = False
                    error_msg = 'job timeout'

            elif j['command'] == 'iperf':

                ##
                # setup second node
                result_dst = remote.setup(j['parameters']['dst'])

                if not result_dst['status']:

                    logger.info("%s : Failed SSH access (%s)" % (j['parameters']['dst'], result_dst['message']))
                    ret = False

                else:

                    # server (thread)
                    remote_command_server = "iperf.py -s"
                    ts = threading.Thread(target=remote_worker, args=(j['node'], remote_command_server))
                    ts.start()
                    logger.info("Running job '%s' on %s" % (remote_command_server, j['node']))

                    time.sleep(2)

                    # client
                    remote_command_client = "iperf.py -c %s %s" % (j['node'], j['parameters']['arg'])
                    logger.info("Running job '%s' on %s" % (remote_command_client, j['parameters']['dst']))

                    try:
                        ret = json.loads(remote_worker(j['parameters']['dst'], remote_command_client))
                    except TimeoutError:
                        ret = False
                        error_msg = 'job timeout'

                    # wait for the thread to finish
                    ts.join()

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
                logger.info("Command executed, result: %s" % (upd))
            else:
                upd = {
                    'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'jobstatus': 'finished',
                    'message': error_msg,
                    'returnstatus': 1,
                    'stdout': '',
                    'stderr': 'unknown command'
                }
                logger.error("Command %s not found" % (j['command']))

        r.table('jobs').get(job).update(upd).run(c)
