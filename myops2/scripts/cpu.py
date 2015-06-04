#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import json


if __name__ == '__main__':

    cpu = {
           "cpus": 1
    }

    cpuid = None

    with open('/proc/cpuinfo') as f:
        for line in f:
            if not line.strip():
                # end of one processor
                pass
            else:
                if line.startswith('physical id'):
                    cpuid = int(line.split(':')[1].strip()) + 1
                    if cpu["cpus"] < cpuid:
                        cpu["cpus"] = cpuid

                if line.startswith('model name'):
                    cpu["model"] = line.split(':')[1].strip()

                if line.startswith('cpu cores'):
                    cpu["cores"] = line.split(':')[1].strip()

                if line.startswith('siblings'):
                    cpu["threads"] = line.split(':')[1].strip()

                if line.startswith('cpu MHz'):
                    cpu["speed"] = line.split(':')[1].strip()

                if line.startswith('cache size'):
                    cpu["cache"] = line.split(':')[1].strip()

    print json.dumps(cpu)