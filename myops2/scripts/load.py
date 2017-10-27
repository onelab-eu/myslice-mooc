#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import os, json


if __name__ == '__main__':

    load = os.getloadavg()
    print json.dumps({
                "1"     : round(load[0],2),
                "5"     : round(load[1],2),
                "15"    : round(load[2],2)
            })