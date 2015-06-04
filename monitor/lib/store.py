import os
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

RDB_HOST = 'localhost'
RDB_PORT = 28015
RDB_DB = 'myops2'


def setup():
    """Return Boolean

    Initial setup
    """
    try:
        connection = connect()
    except RqlDriverError as e:
        print e
        print "RethinkDB database not configured or not reachable"
        exit(1)

    try:
        r.db_create(RDB_DB).run(connection)
        print 'MyOps2 database setup completed.'
    except RqlRuntimeError:
        print 'MyOps2 database already exists.'

    try:
        r.db(RDB_DB).table_create('resources', primary_key='hostname').run(connection)
        print 'MyOps2 table resources setup completed.'
    except RqlRuntimeError:
        print 'MyOps2 table resources already exists.'
    finally:
        connection.close()


def connect(host=RDB_HOST, port=RDB_PORT):
    return r.connect(host, port)


def select(id=None, filter=None, c=None):
    if not c:
        c = connect()
    x = r.db(RDB_DB).table('resources')
    if id:
        x = r.get(id)
    if filter:
        pass
    return x.run(c)


def update(data, c=None):
    if not c:
        c = connect()
    r.db(RDB_DB).table('resources').insert(data, conflict='update').run(c)

def changes(c=None):
    if not c:
        c = connect()
    return r.db(RDB_DB).table('resources').changes().run(c)
