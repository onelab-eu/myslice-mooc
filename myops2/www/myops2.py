from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import psycopg2, psycopg2.extras

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


@app.route('/')
def status():
    try:
        conn = psycopg2.connect("dbname='myops2' user='myops2' host='localhost' password='IChVVyCbxrhA'")
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except:
            raise Exception("Unable to connect to the database")
    
    try:
        cursor.execute("select * from status;")
        resources = cursor.fetchall()
    except Exception as e:
        raise Exception("Unable to retrieve data from database: %s" % e)
    
    return render_template('status.html', resources=resources)


if __name__ == '__main__':
    app.run()