#!/usr/bin/env python

from scapy.all import *
import sys
import time
from datetime import datetime, date
import json


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


if __name__ == '__main__':

    arguments = sys.argv
    num = arguments[len(arguments) - 1]

    directory = "/home/upmc_kvermeulen/ip_ids/"

    destinations_tmp_file = directory + "destinations" + str(num)

    results = []

    with open(destinations_tmp_file) as destinations:
        for ip in destinations:
            ip = ip.strip('\n')
            try:
                for i in range(0, 5):
                    time_sent = time.time()
                    rep       = sr1(IP(dst=ip) / ICMP(), timeout=1, verbose=False)
                    time_rcv  = time.time()
                    if rep:
                        id        = rep[0].id
                        ip_src    = rep[0].dst    # ip_src = rep[0].dst because it's the response from the dst
                        ip_dst    = rep[0].src    # ip_dst = rep[0].src because it's the response from the dst

                        results.append({
                            "node": ip_src,
                            "destination": ip_dst,
                            "sent": json.dumps(time_sent, default=json_serial),
                            "received": json.dumps(time_rcv, default=json_serial),
                            "ip_id": id,
                            "started": json.dumps(datetime.now(), default=json_serial)

                        })

            except AttributeError:
                print "Je suis dans AttributeError"
                continue

    print json.dumps(results)
