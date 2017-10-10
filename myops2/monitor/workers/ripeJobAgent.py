from datetime import datetime, timedelta
from ripe.atlas.cousteau import Ping, Traceroute, AtlasSource, AtlasCreateRequest, AtlasRequest
import threading
import time
import logging
from myops2.lib.queue import OrderedSetQueue
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError
from myops2.settings import Config
from myops2.lib.store import connect

logger = logging.getLogger(__name__)

ATLAS_API_KEY = "51d05d93-dfa7-4c4d-b78c-8e719e73cfbb"

threads_results = []

c = connect()


def createSource(nodeID):
    source = AtlasSource(
        type="probes",
        value=str(nodeID),
        requested=1
    )

    logger.info("Source created")
    return source


def createRequest(source, request, job, input):
    atlas_request = AtlasCreateRequest(
        start_time=datetime.utcnow(),
        key=ATLAS_API_KEY,
        measurements=[request],
        sources=[source],
        is_oneoff=True
    )
    logger.info("Request created")

    (is_success, response) = atlas_request.create()

    if (is_success):
        logger.info("Request launched")
        logger.info("Measurement id : " + str(response['measurements'][0]))
        input.put((response['measurements'][0], job))
        return 1
    else:
        logger.info("Error : Request creation")
        logger.info(str(response))
        return 0


def createMeasurement(source, dest, type, job, input):
    msm = ""
    if (type == "ping"):
        msm = Ping(af=4, target=dest, description="Ping request")
        logger.info("Ping created")

    if (type == "traceroute"):
        msm = Traceroute(
            af=4,
            target=dest,
            description="TracerouteRequest",
            protocol="ICMP",
        )
        logger.info("Traceroute created")

    if msm == "" or createRequest(source, msm, job, input) == 0:
        r.table('jobs').get(job).update({
            'started': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
            'jobstatus': 'error',
            'message': 'Cannot create request'
        }).run(c)
        return


def fetchResult(msm_id):
    """
        Function to fetch results from ripe server
    """
    url_path = "/api/v2/measurements/" + str(msm_id)
    request = AtlasRequest(**{"url_path": url_path})
    response = []
    (is_success, response) = request.get()
    if not is_success:
        logger.error("Problem on URL request")
        return (False, ["Cannot fetch results"])
    else:
        if response["status"]["name"] == "No suitable probes":
            logger.eorro("msm " + str(msm_id) + " : No suitable probes")
            return (False, ["No suitable probes"])
    url_path = "/api/v2/measurements/" + str(msm_id) + "/results"
    request = AtlasRequest(**{"url_path": url_path})
    response = []
    (is_success, response) = request.get()
    return (is_success, response)


def waitForResults(id, input):
    pending = []
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
            (is_success, response) = fetchResult(j_info[0])
            if not is_success:
                # Stocker messag erreur
                logger.info("Result fetcher " + str(id) + ": measurement " + str(j_info[0]) + " can't be fetched")
                r.table('jobs').get(j_info[1]).update({
                    'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'jobstatus': 'error',
                    'message': response[0]
                }).run(c)
                continue

            if response != []:
                # Stocker resultats
                logger.info("Result fetcher " + str(id) + ": result for measurement " + str(j_info[0]) + ": \n" + str(
                    response) + "\n")
                r.table('jobs').get(j_info[1]).update({
                    'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'jobstatus': 'completed',
                    'message': 'Done',
                    'stdout': str(response)
                }).run(c)
            else:
                logger.info("Result fetcher " + str(id) + ": measurement " + str(j_info[0]) + " still on going");
                tmp.append(j_info)
        pending = tmp
        time.sleep(5)


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

    inputResults = startResultThread(num)

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

        if not 'arg' in j['parameters']:
            j['parameters']['arg'] = ""

        source = createSource(j['node'])
        if j['command'] == 'ping':
            createMeasurement(source, j['parameters']['dst'], "ping", job, inputResults)
        elif j['command'] == 'traceroute':
            createMeasurement(source, j['parameters']['dst'], "traceroute", job, inputResults)
        else:
            logger.info("Job: %s measurement type unknown" % (job,))
            r.table('jobs').get(job).update({
                'completed': datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                'jobstatus': 'error',
                'message': 'measurement type unknown'
            }).run(c)
