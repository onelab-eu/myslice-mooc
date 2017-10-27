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

    traceroute = subprocess.Popen(
                ["traceroute"] + arguments[1:],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
                )
    out, err = traceroute.communicate()

    print json.dumps({
        'returnstatus': traceroute.returncode,
        'stdout': out,
        'stderr': err
    })