import rethinkdb as r
import json
import resource
from pylab import *
from datetime import datetime
from graph_tool.all import *
from graph.graph_builder import *
from graph.graph_utils import *
import re
from datetime import datetime, timedelta
import random


# DONT FORGET TO CREATE /home/upmc_kvermeulen  /home/upmc_kvermeulen/tmp and /home/upmc_kvermeulen/ip_ids directories

if __name__ == '__main__':

    localport = 28015
    tmp_private_ip = "192.168.1"

    try:
        db_server = "localhost"
        db_name = "myops2"
        db_port = localport
        conn = r.connect(db_server, db_port)

        nslookup = {}
        as_prefixes = []
        as_ips = []

        options = {"graph_type": "as_mapping",
                   "sources_public_ips": "data/mapping.json",
                   "as_prefixes": "data/telia_prefixes",
                   "as_ips": "data/telia_ips",
                   "debug": True}

        ips_from_db = []
        # Get the mapping.json between nodes name and public ip
        with open(options["sources_public_ips"]) as mapping:
            nslookup = json.load(mapping)

        with open(options["as_prefixes"]) as prefixes:
            for prefix in prefixes:
                as_prefixes.append(prefix.strip("\n"))

        with open(options["as_ips"]) as ips:
            for ip in ips:
                as_ips.append(ip.strip("\n"))

        sources = []

        destinations = as_ips

        for k in nslookup.keys():  # Ajout des sources dans la liste "sources"
            sources.append(k)

        already_in_list = []
        g = Graph()

        feed = r.db(db_name).table('results').changes().run(conn)

        for s_d_snapshot in feed:
            try:
                g = compute_graph_from_db_s_d(s_d_snapshot["new_val"], nslookup, as_prefixes, options)
                if len(g.get_vertices() != 0):
                    ip = g.vertex_properties["ip_address"]

                    for v in g.vertices():
                        if is_ip_in_as(ip[v], as_prefixes):  # if in Telia's AS -> we put the ip in the list
                            if ip[v] in already_in_list:
                                continue
                            if re.match(r'^1/16:', ip[v]) is not None:
                                continue
                            if ip[v] == "* * *":
                                continue

                            already_in_list.append(ip[v])

                            ips_from_db.append(ip[v])

                if len(ips_from_db) > 15:

                    body = {
                        "node": random.choice(sources),
                        "type": "ple",
                        "command": "icmp",
                        "parameters": {
                            "dst": ips_from_db[:],
                            "arg": ""
                        },
                        "jobstatus": "waiting",
                        "message": "waiting to be executed",
                        "created": r.expr(datetime.now(r.make_timezone('01:00'))),
                        "started": "",
                        "completed": "",
                        "returnstatus": "",
                        "stdout": "",
                        "stderr": ""
                    }

                    ips_from_db[:] = []
                    r.db(db_name).table('jobs').insert(body).run(conn)

            except Exception:
                print "[Extract ip's] Exception -> Compute Graph"
                continue
    finally:
        print "[Extract IP'S] Done !"

