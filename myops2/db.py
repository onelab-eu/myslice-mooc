import sys, os, signal, time
import psycopg2

class db(object) :

    def __init__(self):
        try:
            self.conn = psycopg2.connect("dbname='myops2' user='myops2' host='localhost' password='IChVVyCbxrhA'")
            self.cursor = self.conn.cursor()
        except:
            raise Exception("Unable to connect to the database")

    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()
        
    ''' update info for the resource '''
    def update_resource(self, resource):

        if not resource.hostname :
            raise Exception("Resource name must be specified")
    
        try:
            self.cursor.execute("SELECT hostname FROM resources WHERE hostname='%s'" % (resource.hostname))
            if not self.cursor.fetchone() :
                print "+=> Inserting %s" % (resource.hostname)
                self.cursor.execute("INSERT INTO resources (hostname,site) VALUES ('%s','%s')" % (resource.hostname,resource.site_name)) 
        except Esception as e:
            raise Exception("Unable to update database: %s" % e)

    ''' retrieve the resources to monitor '''
    def monitor_resources(self):
        try:
            cursor.execute("SELECT hostname FROM resources WHERE timestamp > current_timestamp - interval '15 minutes'")
            rows = cursor.fetchall()
            return rows
        except:
            raise Exception("Unable to retrieve data from database")
    
    def status_resource(self, resource):
        cursor.execute("INSERT INTO monitor (hostname,status,timestamp) VALUES ('%s','%s',current_timestamp)" % (resource.hostname,resource.status))
