import json, logging
import decimal
from datetime import date, datetime
from tornado import web, gen

from myops2.settings import Config
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

logger = logging.getLogger(__name__)

# handles serialization of datetime in json
#DateEncoder = lambda obj: obj.strftime("%B %d, %Y %H:%M:%S") if isinstance(obj, datetime.datetime) else None
DateEncoder = lambda obj: obj.isoformat() if isinstance(obj, datetime) else None

# support converting decimal in json
json.encoder.FLOAT_REPR = lambda o: format(o, '.2f')

# handles decimal numbers serialization in json
class DecimalEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, decimal.Decimal):
            return (str(o) for o in [o])
        return super(DecimalEncoder, self)._iterencode(o, markers)

def connect():
    try :

        r.set_loop_type("tornado")

        return r.connect(host=Config.rethinkdb["host"], port=Config.rethinkdb["port"], db=Config.rethinkdb['db'])

    except r.RqlDriverError :

        logger.error("Can't connect to RethinkDB")
        raise SystemExit("Can't connect to RethinkDB")


# class VersionHandler(web.RequestHandler):
#     def get(self):
#         response = { 'version': '3.5.1',
#                      'last_build':  date.today().isoformat() }
#         self.write(response)
#
# class GetGameByIdHandler(web.RequestHandler):
#     def get(self, id):
#         response = { 'id': int(id),
#                      'name': 'Crazy Game',
#                      'release_date': date.today().isoformat() }
#         self.write(response)

class Resources(web.RequestHandler):

    @gen.coroutine
    def get(self, *args):
        resources = []

        connection = yield connect()

        cursor = yield r.table('resources').run(connection)

        while (yield cursor.fetch_next()):
            item = yield cursor.next()
            resources.append(item)

        #self.finish()
        #id = self.get_argument("id")
        #value = self.get_argument("value")
        #data = {"id": id, "value" : value}

        #self.write({"resources": resources})
        self.write(json.dumps({"resources": resources}, cls=DecimalEncoder, default=DateEncoder))

        #for c in cl:
        #    c.write_message(data)

    @web.asynchronous
    def post(self):
        pass

