#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import os, json


if __name__ == '__main__':

    pids = 0
    for subdir in os.listdir('/proc'):
        if subdir.isdigit():
            pids += 1

    print pids