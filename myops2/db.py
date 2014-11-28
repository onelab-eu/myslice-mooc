import sys, os, signal, time
import psycopg2

def connect():
    try:
        conn = psycopg2.connect("dbname='myops2' user='myops2' host='localhost' password='IChVVyCbxrhA'")
    except:
        print "Unable to connect to the database"
        return False
    return conn
        
def update(resource):
    
    if not resource.hostname :
        print "Resource name must be specified"
        return False
    
    conn = connect()
    if conn :
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT hostname FROM resources WHERE hostname='%s'" % (resource.hostname))
            if not cursor.fetchone() :
                cursor.execute("INSERT INTO resources (hostname,site) VALUES ('%s','%s')" % (resource.hostname,resource.site_name))
            
            cursor.execute("INSERT INTO monitor (hostname,status,timestamp) VALUES ('%s','%s',current_timestamp)" % (resource.hostname,resource.status))
            
            conn.commit()
            conn.close()
        except:
            print "Unable to update database"
            return False
    return True