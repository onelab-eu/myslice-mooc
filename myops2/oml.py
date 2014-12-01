from datetime import datetime
from oml4py import OMLBase

'''
    resource is the resource name (e.g. hostname)
    status is 1 or 0 (up or down)
'''
def availability(resource, status) :
    oml = OMLBase("availability","PLE","PLETestbed","tcp:localhost:3003")
    
    oml.addmp("sss", "node:string up:double last_check:string")
    oml.start()
    
    oml.inject("sss", (resource, status, datetime.now().isoformat()  + "+01:00"))
    
    oml.close()