import requests
import json
import time
import rethinkdb as r
from myops2.lib.store import connect
import logging

logger = logging.getLogger(__name__)

class monitor:
    def __init__ (self):
        self.nodesInfoList = []
        
    def nodeList(self, next=None):
        while next != None:
            r = requests.get(next) # Requete sur l'url suivant             
                
            if r.status_code != 200:
                logger.error("Error : Request error")
                break
    
            text = json.loads(r.text)
            results = text['results']
            next = text['next']       
            self.nodesInfoList.append(results)

    def insert (self):
        c = connect()
        for lr in self.nodesInfoList:
            for k in lr:
                r.table('resources').insert(k, conflict='update').run(c)
        c.close()
        return True
    
    def filtre(self):
        for i in range (len(self.nodesInfoList)):
            
            for j in range(len(self.nodesInfoList[i])):
                del self.nodesInfoList[i][j]["tags"]
                del self.nodesInfoList[i][j]["asn_v4"]
                del self.nodesInfoList[i][j]["asn_v6"]
                del self.nodesInfoList[i][j]["geometry"]
                del self.nodesInfoList[i][j]["description"]
                self.nodesInfoList[i][j]["testbed"] = 'ripe'
                self.nodesInfoList[i][j]["hostname"] = self.nodesInfoList[i][j].pop("id")
               
        return "Filtre le noeud par etat\n"
    
def monitor_thread (url,temps):
    m = monitor()
    while True:
        m.nodeList(url)
        m.filtre() 
        m.insert()
        time.sleep(temps)

if (__name__ == 'a__main__'):
    m = monitor()
    f = open ("/tmp/RipeListNodes.txt","w")
    m.nodeList()
    print('\n\n\n')
    print(m.nodesInfoList)
