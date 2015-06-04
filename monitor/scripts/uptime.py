#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import os, json
from datetime import timedelta

if __name__ == '__main__':

    with open('/proc/uptime', 'r') as f:
        seconds = float(f.readline().split()[0])
        text = str(timedelta(seconds = seconds))
        print json.dumps({
            "seconds": seconds,
            "text": text
        })