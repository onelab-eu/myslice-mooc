import sys, os, signal, time, logging
import psycopg2, psycopg2.extras

class db(object) :

    def __init__(self):
        try:
            self.conn = psycopg2.connect("dbname='myops2' user='myops2' host='localhost' password='IChVVyCbxrhA'")
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
                logging.info("+=> Inserting %s" % (resource.hostname))
                self.cursor.execute("INSERT INTO resources (hostname,site) VALUES ('%s','%s')" % (resource.hostname,resource.site))
                self.cursor.execute("INSERT INTO monitor (hostname,status,timestamp) VALUES ('%s','new',current_timestamp - interval '15 minutes')" % (resource.hostname))
        except Exception as e:
            raise Exception("Unable to update database: %s" % e)

    ''' retrieve the resources to monitor '''
    def select_resources(self):
        try:
            self.cursor.execute("select * from status where last_checked < current_timestamp - interval '15 minutes';")
            rows = self.cursor.fetchall()
            return rows
        except Exception as e:
            raise Exception("Unable to retrieve data from database: %s" % e)
    
    def status_resource(self, hostname, status):
        try :
            self.cursor.execute("INSERT INTO monitor (hostname,status,timestamp) VALUES ('%s','%s',current_timestamp)" % (hostname,status))
        except Exception as e:
            raise Exception("Unable to insert data into database: %s" % e)

    def info_resource(self, hostname, info):
        c = []
        sql = "UPDATE resources SET "
        for k,i in info.iteritems():
            c.append("%s='%s'" % (k, i))
        sql += ",".join(c)
        sql = " WHERE hostname = '%s'" % (hostname)
        try :
            self.cursor.execute(sql)
        except Exception as e:
            raise Exception("Unable to update data into database: %s" % e)