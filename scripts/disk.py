#!/usr/bin/env python

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import os, json, re, glob
from datetime import timedelta

if __name__ == '__main__':

    regex = "(sd[a-z]|mmcblk*)"
    pattern = re.compile(regex)
    devices = []

    for device in glob.glob('/sys/block/*'):
        if pattern.match(os.path.basename(device)):
            nr_sectors = open(device + '/size').read().rstrip('\n')
            sect_size = open(device + '/queue/hw_sector_size').read().rstrip('\n')
            # The sect_size is in bytes, so we convert it to GiB and then send it back
            size = round((float(nr_sectors) * float(sect_size)) / (1024.0 * 1024.0 * 1024.0), 1)
            devices.append({
                "name": device,
                "size": size
            })

    print json.dumps(devices)