from datetime import datetime
from oml4py import OMLBase

'''
    resource is the resource name (e.g. hostname)
    status is 1 or 0 (up or down)
'''
def availability(resource, status) :
    # TUB server
    oml = OMLBase("myops2","PLE","PLETestbed","tcp:193.175.132.241:3003")
    
    oml.mpprefix = False
    
    oml.addmp("availability", "node:string up:double last_check:string")
    oml.start()
    
    oml.inject("availability", (resource, status, datetime.now().isoformat()  + "+01:00"))
    
    oml.close()