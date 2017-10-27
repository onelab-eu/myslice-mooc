#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import json
import sys
import subprocess


if __name__ == '__main__':

    arguments = sys.argv
    hostname = arguments[1:]

    ping = subprocess.Popen(
                ["sudo","ping", "-c", "5"] + arguments[1:],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
                )
    out, err = ping.communicate()

    print json.dumps({
        'returnstatus': ping.returncode,
        'stdout': out,
        'stderr': err
    })