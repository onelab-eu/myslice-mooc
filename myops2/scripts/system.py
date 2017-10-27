#!/usr/bin/env python 

#
# Reads system information and returns them as a structure json string
#
# (c) 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
#

import platform, json

  
if __name__ == '__main__':
    
    system = {
        "system"        : platform.system(),
        "node"          : platform.node(), 
        "release"       : platform.release(), 
        "version"       : platform.version(), 
        "machine"       : platform.machine(), 
        "processor"     : platform.processor(),
        "distribution"  : {
                "name"      : platform.linux_distribution()[0],
                "version"   : platform.linux_distribution()[1],
                "title"     : platform.linux_distribution()[2] 
        }
        
    }
    
    print json.dumps(system)