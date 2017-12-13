from datetime import datetime, timedelta
from ripe.atlas.cousteau import Ping, Traceroute, AtlasSource, AtlasCreateRequest, AtlasRequest, AtlasStopRequest
import threading
import time
import logging
from myops2.lib.queue import OrderedSetQueue
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError
from myops2.settings import Config
from myops2.lib.store import connect
from datetime import timedelta

cv = threading.Condition()
logger = logging.getLogger(__name__)
running_ripe_jobs = 0
RIPE_CONCURRENT_LIMIT = 25
CREDITS_TOTAL_MEASUREMENTS = 0
TOTAL_MEASUREMENTS = 684 #Sources * Destinations defined in the sender.py configuration file

ATLAS_API_KEYS = ["51d05d93-dfa7-4c4d-b78c-8e719e73cfbb","4943e4a5-5a20-4e1b-a090-098873772fa9"]
ATLAS_API_KEY = ATLAS_API_KEYS[1]

threads_results = []

def createSource(nodeID):
    source = AtlasSource(
        type="probes",
        value=str(nodeID),
        requested=1
    )

    logger.info("Source created")
    return source


def createRequest(source, request, job, input):
    now = datetime.utcnow()
    atlas_request = AtlasCreateRequest(
        start_time=now+timedelta(minutes=6),
        key=ATLAS_API_KEY,
        measurements=[request],
        response_timeout = 15,
        sources=[source],
        is_oneoff=True
    )
    logger.info("Request created")
    with cv:
        (is_success, response) = atlas_request.create()
        time.sleep(0.5)

    if (is_success):
        logger.info("Request launched")
        logger.info("Measurement id : " + str(response['measurements'][0]))
        input.put((response['measurements'][0], job, now))
        return 1
    else:
        logger.error("Error : Request creation")
        logger.error(str(response))
        return 0


def createMeasurement(c, source, dest, type, job, input):
    msm = ""
    if (type == "ping"):
        msm = Ping(af=4, target=dest, description="Ping request")
        logger.info("Ping created")

    if (type == "traceroute"):
        msm = Traceroute(
            af=4,
            target=dest,
            description="TracerouteRequest",
            # TODO Pass the protocol as a parameter
            protocol="ICMP",
        )
        logger.info("Traceroute created")

    if msm == "" or createRequest(source, msm, job, input) == 0:
        r.table('jobs').get(job).update({
            'started': r.expr(datetime.now(r.make_timezone('01:00'))),
            'jobstatus': 'error',
            'message': 'Cannot create request'
        }).run(c)
        with cv:
            global running_ripe_jobs
            running_ripe_jobs = running_ripe_jobs - 1
        return


def fetchResult(msm_id):
    """
        Function to fetch results from ripe server
    """
    url_path = "/api/v2/measurements/" + str(msm_id)
    request = AtlasRequest(key=ATLAS_API_KEY, url_path=url_path, headers={"Cache-Control": "no-cache "})


    response = []
    (is_success, response) = request.get()
    status_name = response["status"]["name"]

    if not is_success:
        logger.error("Problem on URL request")
        return (False, ["Cannot fetch results"])
    else:
        if status_name == "No suitable probes":
            logger.error("msm " + str(msm_id) + " : No suitable probes")
            return (False, ["No suitable probes"])
    if status_name == "Stopped":
        url_path = "/api/v2/measurements/" + str(msm_id) + "/results"
        request = AtlasRequest(**{"url_path": url_path})
        result_response = []
        (is_success, result_response) = request.get()
        return (is_success, result_response)
    response = []
    return (is_success, response)

def waitForResults(id, input):
    pending = []
    try :
        c = r.connect(host=Config.rethinkdb["host"], port=Config.rethinkdb["port"], db=Config.rethinkdb['db'])
    except r.RqlDriverError :
        logger.error("Can't connect to RethinkDB")
        raise SystemExit("Can't connect to RethinkDB")
    while (True):
        try:
            while (True):
                job_info = input.get(False)
                pending.append(job_info)
                logger.info("Result fetcher " + str(id) + ": " + str(job_info[0]) + "\'s results to fetch")
        except Exception:
            pass

        tmp = []

        for j_info in pending:

            logger.info("Result fetcher " + str(id) + ": Fetching measurement " + str(j_info[0]) + " results")
            # j_info[0] corresponds to the msm_id
            (is_success, response) = fetchResult(j_info[0])
            if not is_success:
                # Stocker messag erreur
                logger.info("Result fetcher " + str(id) + ": measurement " + str(j_info[0]) + " can't be fetched")
                r.table('jobs').get(j_info[1]).update({
                    'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                    'jobstatus': 'error',
                    'message': response[0]
                }).run(c)
                global running_ripe_jobs
                with cv:
                    running_ripe_jobs = running_ripe_jobs - 1
                    cv.notifyAll()

                continue
            # TODO check len(response)
            if response != []:
                # Stocker resultats
                logger.info("Result fetcher " + str(id) + ": result for measurement " + str(j_info[0]) + ": \n" + str(
                    response) + "\n")

                r.table('jobs').get(j_info[1]).update({
                    'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                    'jobstatus': 'finished',
                    'message': 'Done',
                    'stdout': str(response)
                }).run(c)
                global running_ripe_jobs
                with cv:
                    running_ripe_jobs = running_ripe_jobs - 1
                    cv.notifyAll()

            else:
                logger.info("Result fetcher " + str(id) + ": measurement " + str(j_info[0]) + " still on going");
                tmp.append(j_info)

        pending = tmp
        time.sleep(310)



def startResultThread(num):
    """
        Function to launch thread to fetch results
    """
    input = OrderedSetQueue()
    t = threading.Thread(target=waitForResults, args=(num, input))
    t.daemon = True
    threads_results.append(t)
    t.start()

    logger.info("Thread started")
    return input


def waitingForThreads():
    """
        Fonction to wait for thread completion
    """
    logger.info("Waiting for threads completion")
    for t in threads_results:
        t.join()

    logger.info("All thread have finished")


def ripe_process_job(num, input):
    """
        Function to launch the job agent
    """
    logger.info("Agent %s starting" % num)

    try :
        c = r.connect(host=Config.rethinkdb["host"], port=Config.rethinkdb["port"], db=Config.rethinkdb['db'])
    except r.RqlDriverError :
        logger.error("Can't connect to RethinkDB")
        raise SystemExit("Can't connect to RethinkDB")

    inputResults = startResultThread(num)

    while True:
        job = input.get()
        logger.info("Agent %s processing job %s" % (num, job))

        j = r.table('jobs').get(job).run(c)

        logger.info("Job: %s" % (j,))


        if not 'arg' in j['parameters']:
            j['parameters']['arg'] = ""

        source = createSource(j['node'])
        if j['command'] == 'ping':
            createMeasurement(source, j['parameters']['dst'], "ping", job, inputResults)
        elif j['command'] == 'traceroute':
            global running_ripe_jobs
            with cv:
                while running_ripe_jobs >= RIPE_CONCURRENT_LIMIT:
                    cv.wait()
                running_ripe_jobs = running_ripe_jobs + 1


            r.table('jobs').get(job).update({
                'started': r.expr(datetime.now(r.make_timezone('01:00'))),
                'jobstatus': 'running',
                'message': 'executing job'
            }).run(c)

            createMeasurement(c, source, j['parameters']['dst'], "traceroute", job, inputResults)



        else:
            logger.info("Job: %s measurement type unknown" % (job,))
            r.table('jobs').get(job).update({
                'completed': r.expr(datetime.now(r.make_timezone('01:00'))),
                'jobstatus': 'error',
                'message': 'measurement type unknown'
            }).run(c)


if __name__ == '__main__':
    #delete_request = AtlasStopRequest(msm_id="10359621", key=ATLAS_API_KEY)

    request = fetchResult("10360807")
