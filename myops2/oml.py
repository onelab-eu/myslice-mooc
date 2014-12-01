from datetime import datetime
from oml4py import OMLBase

'''
    resource is the resource name (e.g. hostname)
    status is 1 or 0 (up or down)
'''
def availability(resource, status) :
    oml = OMLBase("","PLE","PLETestbed","tcp:localhost:3003")
    
    oml.addmp("availability", "node:string up:double last_check:string")
    oml.start()
    
    oml.inject("availability", (resource, 1, datetime.now().isoformat()  + "+01:00"))
    
    oml.close()