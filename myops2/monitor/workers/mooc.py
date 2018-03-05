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

# Helper function merge dictionnaries

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def handle_timeout(signum, frame):
    raise TimeoutError(os.strerror(errno.ETIME))


signal.signal(signal.SIGALRM, handle_timeout)


class TimeoutError(Exception):
    pass


def remote_worker(num, command, hostname, script, destinations, path_to_dst, semaphore_map):
    # timeout after 2h
    signal.alarm(7200)

    logger.info("Running job '%s' on %s" % (script, hostname))
    ret = {}
    try:
        result = remote.script(num, hostname, script, destinations, path_to_dst, semaphore_map)
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
        if command == "paris-traceroute":
            logger.info("job '%s' completed on %s" % (script, hostname))
            results = []
            list_result = json.loads(result)
            for r in list_result:
                try:
                    logger.info("JSON: %s", result)

                except Exception, msg:
                    logger.error("JSON error: %s" % (msg,))
                    it = {
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': '',
                        "destination": r["destination"]
                    }
                    results.append(it)
                else:
                    it = {
                        'jobstatus': 'finished',
                        'message': 'job completed',
                        'returnstatus': r['returnstatus'],
                        'stdout': r['stdout'],
                        'stderr': r['stderr'],
                        "destination": r["destination"]
                    }
                    results.append(it)
            ret = {
                'jobstatus': 'finished',
                'message': 'job completed',
                'returnstatus': 0,
                "results": results
            }
        elif command == "icmp":
            return json.loads(result)
    finally:
        signal.alarm(0)

    return ret


def process_job(num, input, semaphore_map):
    """
    This worker will try to check for resource availability

    """

    logger.info("Agent %s starting" % num)

    try:
        c = r.connect(host=Config.rethinkdb["host"], port=Config.rethinkdb["port"], db=Config.rethinkdb["db"])
    except r.RqlDriverError :
        logger.error("Can't connect to RethinkDB")
        raise SystemExit("Can't connect to RethinkDB")

    while True:
        job = input.get()
        logger.info("Agent %s processing job %s" % (num, job))

        j = r.table('jobs').get(job).run(c)

        logger.info("Job: %s" % (j,))

        r.table('jobs').get(job).update({
            'started': r.expr(datetime.now(r.make_timezone('01:00'))),
            'jobstatus': 'running',
            'message': 'executing job'
        }).run(c)

        results = []
        errors = []

        result = remote.setup(j['node'], semaphore_map)

        if not result['status']:
            logger.info("%s : Failed SSH access (%s)" % (j['node'], result['message']))
            upd = {
                'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                'jobstatus': 'error',
                'message': 'node not reachable',
                'returnstatus': 1,
                'stdout': '',
                'stderr': result['message']
            }
            
        else:
            if not 'arg' in j['parameters']:
                j['parameters']['arg'] = ""

            if j['command'] == 'ping':
                command = 'ping'

                remote_command = '%s.py %s %s' % (command, j['parameters']['arg'], j['parameters']['dst'])

                try:
                    ret = remote_worker(j['node'], remote_command)
                except Exception, msg:
                    logger.error("EXEC error: %s" % (msg,))
                    upd = {
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': "execution error %s" % (msg)
                    }
                    logger.error("execution error %s" % (msg))
                else:
                    upd = {
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
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
                    ret = remote_worker(j['node'], remote_command, semaphore_map)
                except Exception, msg:
                    logger.error("EXEC error: %s" % (msg,))
                    upd = {
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': "execution error %s" % (msg)
                    }
                    logger.error("execution error %s" % (msg))
                else:
                    upd = {
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
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
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
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
                            'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                            'jobstatus': 'error',
                            'message': 'job error',
                            'returnstatus': 1,
                            'stdout': '',
                            'stderr': "execution error %s" % (msg)
                        }
                        logger.error("execution error %s" % (msg))
                    else:
                        upd = {
                            'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                            'jobstatus': ret['jobstatus'],
                            'message': ret['message'],
                            'returnstatus': ret['returnstatus'],
                            'stdout': ret['stdout'],
                            'stderr': ret['stderr']
                        }
                        logger.info("Command executed, result: %s" % (upd))

            elif j['command'] == 'wget':
                command = 'wget'

                remote_command = '%s.py %s %s' % (command, j['parameters']['arg'], j['parameters']['dst'])

                try:
                    ret = remote_worker(j['node'], remote_command)
                except Exception, msg:
                    logger.error("EXEC error: %s" % (msg,))
                    upd = {
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': "execution error %s" % (msg)
                    }
                    logger.error("execution error %s" % (msg))
                else:
                    upd = {
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                        'jobstatus': ret['jobstatus'],
                        'message': ret['message'],
                        'returnstatus': ret['returnstatus'],
                        'stdout': ret['stdout'],
                        'stderr': ret['stderr']
                    }
                    logger.info("Command executed, result: %s" % (upd))

            elif j["command"] == "paris-traceroute":
                command = 'paris-traceroute'

                # DONT FORGET TO CREATE /home/upmc_kvermeulen  /home/upmc_kvermeulen/tmp and /home/upmc_kvermeulen/ip_ids directories

                remote_command = '%s.py %s' % (command, j['parameters']['arg'])
                destinations   = j['parameters']['dst']
                path_to_dst    = "/home/upmc_kvermeulen/tmp/"
                try:
                    ret = remote_worker(num, command, j['node'], remote_command, destinations, path_to_dst, semaphore_map)
                except Exception, msg:
                    logger.error("EXEC error: %s" % (msg,))
                    upd = {
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': "execution error %s" % (msg)
                    }
                    logger.error("execution error %s" % (msg))
                    errors.append(upd)
                else:
                    if "results" in ret:
                        for res in ret["results"]:
                            upd = {
                                'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                                'jobstatus': res['jobstatus'],
                                'message': res['message'],
                                'returnstatus': res['returnstatus'],
                                'stdout': res['stdout'],
                                'stderr': res['stderr'],
                                "destination" : res["destination"]
                            }
                            stderr = res['stderr']
                            if stderr == "":
                                logger.info("Command executed, result: %s" % (upd))
                                results.append(upd)
                            else:
                                errors.append(upd)
                    else:
                        logger.error("EXEC error: %s" % (msg,))
                        upd = {
                            'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                            'jobstatus': 'error',
                            'message': 'job error',
                            'returnstatus': 1,
                            'stdout': '',
                            'stderr': "execution error %s" % (msg)
                        }
                        logger.error("execution error %s" % (msg))

            elif j["command"] == "icmp":
                command = 'icmp'

                remote_command = '%s.py %s' % (command, j['parameters']['arg'])
                destinations   = j['parameters']['dst']

                # DONT FORGET TO CREATE /home/upmc_kvermeulen  /home/upmc_kvermeulen/tmp and /home/upmc_kvermeulen/ip_ids directories

                path_to_dst    = "/home/upmc_kvermeulen/ip_ids/"
                try:
                    ret = remote_worker(num, command, j['node'], remote_command, destinations, path_to_dst, semaphore_map)
                except Exception, msg:
                    logger.error("EXEC error: %s" % (msg,))
                    upd = {
                        'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                        'jobstatus': 'error',
                        'message': 'job error',
                        'returnstatus': 1,
                        'stdout': '',
                        'stderr': "execution error %s" % (msg)
                    }
                    logger.error("execution error %s" % (msg))
                    errors.append(upd)
                else:

                    for res in ret:
                        upd = {
                            'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                             "node": res["node"],
                        "destination": res["destination"],
                        "sent": r.expr(res["sent"]),
                        "received": r.expr(res["received"]),
                        "ip_id": res["ip_id"],
                        "started": r.expr(res["started"])
                        }
                        results.append(upd)

        upd = {
                'jobstatus': 'finished',
                'message': 'job completed',
            }

        r.table('jobs').get(job).update(upd).run(c)

        for result in results:
            document = r.table('jobs').get(job).run(c)
            document.pop("id", None)
            document["parameters"]["dst"] = result["destination"]

            to_insert = merge_two_dicts(document, result)

            table = ""

            if j["command"] == "icmp":
                table = "ip_ids"
                r.table(table).insert(to_insert).run(c)
            elif j["command"] == "paris-traceroute":
                table = "results"
                r.table(table).insert(to_insert).run(c)

        if j["command"] == "paris_traceroute":
            for error in errors:
                document = r.table('jobs').get(job).run(c)
                document.pop("id", None)
                document["parameters"]["dst"] = error["destination"]
                to_insert = merge_two_dicts(document, error)
                r.table("errors").insert(to_insert).run(c)