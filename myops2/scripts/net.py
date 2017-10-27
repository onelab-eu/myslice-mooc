#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import json
from collections import namedtuple

if __name__ == '__main__':
    ''' RX and TX bytes for each of the network devices '''

    with open('/proc/net/dev') as f:
        net_dump = f.readlines()

    device_data={}
    data = namedtuple('data', ['rx', 'tx'])
    for line in net_dump[2:]:
        line = line.split(':')
        if line[0].strip() != 'lo':
            device_data[line[0].strip()] = data(float(line[1].split()[0])/(1024.0*1024.0),
                                                float(line[1].split()[8])/(1024.0*1024.0))

    print json.dumps(device_data)