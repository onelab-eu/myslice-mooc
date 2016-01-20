import json, logging, time
import decimal
from datetime import date, datetime
from tornado import web, gen
import tornado_cors as cors
from tornado_cors import custom_decorator

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

class Resources(cors.CorsMixin, web.RequestHandler):

    def set_default_headers(self):
        # to allow CORS
        self.set_header("Access-Control-Allow-Origin", "*")

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

class Job(cors.CorsMixin, web.RequestHandler):

    def set_default_headers(self):
        # to allow CORS
        self.set_header("Access-Control-Allow-Origin", "*")

    @gen.coroutine
    def get(self, *args):
        jobs = []

        connection = yield connect()

        cursor = yield r.table('jobs').run(connection)

        while (yield cursor.fetch_next()):
            item = yield cursor.next()
            jobs.append(item)

        self.write(json.dumps({"jobs": jobs}, cls=DecimalEncoder, default=DateEncoder))


    @gen.coroutine
    def post(self, *args):
        #post body must be a list
        #jobs = []
        #jobs = tornado.escape.json_decode(self.request.body)
        jobs = json.loads(self.request.body)

        ts = time.time()
        # Adding additional info to the json
        for data in jobs:
            data["jobstatus"]       = "waiting"
            data["message"]         = "waiting to be executed"
            data["created"]         = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            data["started"]         = ""
            data["completed"]       = ""
            data["returnstatus"]    = ""
            data["stdout"]          = ""
            data["stderr"]          = ""

            json.dumps(data)


        connection = yield connect()

        yield r.table('jobs').run(connection)

        rows = yield r.table("jobs").insert(jobs).run(connection)

        ids =[]
        # getting the generated keys from the DB
        for key in rows['generated_keys']:
            ids.append(key)

        self.write(json.dumps({"id": ids}))