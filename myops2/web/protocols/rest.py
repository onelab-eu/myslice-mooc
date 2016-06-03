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

class Resources(cors.CorsMixin, web.RequestHandler):

    def set_default_headers(self):
        # to allow CORS
        self.set_header("Access-Control-Allow-Origin", "*")

    @gen.coroutine
    def get(self, *args):
        resources = []

        cursor = yield r.table('resources').run(self.application.dbconnection)

        while (yield cursor.fetch_next()):
            item = yield cursor.next()
            resources.append(item)

        self.finish(json.dumps({"resources": resources}, cls=DecimalEncoder, default=DateEncoder))


    @web.asynchronous
    def post(self):
        pass

class Job(cors.CorsMixin, web.RequestHandler):

    def initialize(self):
        self.dbconnection = self.application.dbconnection

    def set_default_headers(self):
        # to allow CORS
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")

    @gen.coroutine
    def get(self, id=None):
        jobs = []

        if id is not None:
            logger.info("GET JOB " % (id))
            ret = yield r.table('jobs').get(id).run(self.dbconnection)
            jobs.append(ret)
        else:
            logger.info("GET ALL JOBS")
            cursor = yield r.table('jobs').run(self.dbconnection)

            while (yield cursor.fetch_next()):
                item = yield cursor.next()
                jobs.append(item)

        self.finish(json.dumps({"jobs": jobs}, cls=DecimalEncoder, default=DateEncoder))


    @gen.coroutine
    def post(self, *args):
        #post body must be a list
        #jobs = []
        #jobs = tornado.escape.json_decode(self.request.body)
        jobs = json.loads(self.request.body)

        logger.info("Received %s" % (jobs,))

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
         

        yield r.table('jobs').run(self.dbconnection)

        rows = yield r.table("jobs").insert(jobs).run(self.dbconnection)

        ids =[]
        # getting the generated keys from the DB
        for key in rows['generated_keys']:
            ids.append(key)

        self.finish(json.dumps({"id": ids}))
