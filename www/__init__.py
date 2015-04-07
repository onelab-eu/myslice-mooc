from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import psycopg2, psycopg2.extras

# configuration
#DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
#USERNAME = 'admin'
#PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


@app.route('/')
def status():
    print "test"
    try:
        conn = psycopg2.connect("dbname='myops2' user='myops2' host='localhost' password='IChVVyCbxrhA'")
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except:
        raise Exception("Unable to connect to the database")
    
    try:
        cursor.execute("select distinct on (m.hostname) m.hostname,r.ipv4,r.ipv6,m.timestamp as last_checked,m.status from monitor m left join resources r on (r.hostname = m.hostname) order by m.hostname, m.timestamp desc;")
        resources = cursor.fetchall()
    except Exception as e:
        raise Exception("Unable to retrieve data from database: %s" % e)
    
    return render_template('status.html', resources=resources)


#if __name__ == '__main__':
#    app.run(host='0.0.0.0')
