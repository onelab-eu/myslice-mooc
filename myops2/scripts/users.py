#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import os, subprocess, json, re


if __name__ == '__main__':

    regex = "(^[a-z_][a-z0-9_-]*[$]?)([ ]*)([^ ]*)([ ]*)([^ ]*)([ ]*)(.*)"
    pattern = re.compile(regex)
    users = []

    p = subprocess.Popen(["/usr/bin/w","-sfh"], stdout=subprocess.PIPE)
    for line in iter(p.stdout.readline,''):
        match = pattern.match(line)
        if (match):
            users.append({
                "user": match.group(1),
                "tty": match.group(3),
                "idle": match.group(5),
                "what": match.group(7)
            })
    print json.dumps(users)