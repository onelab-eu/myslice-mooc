#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import json


if __name__ == '__main__':

    meminfo = {}

    with open('/proc/meminfo') as f:
        for line in f:
            mem = line.split(':')[1].strip()[:-3]
            if len(mem) > 0:
                meminfo[line.split(':')[0]] = int(mem) / 1024
            else :
                meminfo[line.split(':')[0]] = 0

    print json.dumps(meminfo)