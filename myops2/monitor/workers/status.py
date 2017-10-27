import logging
from datetime import datetime

import myops2.lib.store as s
import myops2.lib.remote as r

from planetlab.query import Query

logger = logging.getLogger(__name__)

def agent(num, input):
    """
    A thread that will check resource availability and information
    """
    logger.info("Agent %s starting" % num)

    while True:
        resource = input.get() # resource hostname


        '''
            Load node information from the testbed/facility DB (e.g. with SFA or local API)
            We get from there the node status
        '''
        try:
            node = Query('Nodes').hostname(resource).execute().first()
        except Exception as e:
            logger.error("Query error : %s", (e))
        else:
            if not node:
                logger.info("Node disappeared : %s", (node.hostname))

            if not node.enabled:
                #logger.info("(%s) %s is not enabled" % (node.boot, node.hostname))
                availability = 0
                status = "disabled"

            elif not node.is_running():
                #logger.info(" (%s) %s is not running" % (node.boot, node.hostname))
                availability = 0
                status = "down"
            else:
                # if not r:
                #     print "+=> (%s) %s is not accessible" % (node.boot, node.hostname)
                #     availability = 0
                #     status = "no access"
                # else :
                #     print "+=> (%s) %s is ok" % (node.boot, node.hostname)
                availability = 1
                status = "up"
                    #updates info about the node (testing)
                    # d.info_resource(node.hostname, {
                    #     #'ipv4' : node.ip(4),
                    #     'ipv6' : node.ip(6),
                    # })

            '''
                Node access status: e.g. ssh, we try to do a setup on the node and report the result
                We try also with nodes that are marked as disabled or not working anyway
            '''
            try:
                result = r.setup(resource)
            except Exception as e:
                logger.error("Error: %s" % e)
            else:
                if not result['status'] :
                    logger.info("%s : Failed SSH access (%s)" % (resource, result['message']))
                else :
                    logger.info("%s : Setup complete" % (resource))

                s.resource({
                    "hostname": node.hostname,
                    "state": node.boot_state,
                    "access" : result
                })

