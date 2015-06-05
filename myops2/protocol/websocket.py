import json
from tornado import websocket, gen

import rethinkdb as r
r.set_loop_type("tornado")

cl = []

class Api(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in cl:
            cl.append(self)
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"Waiting for changes")
        self.feed()

    def on_close(self):
        if self in cl:
            cl.remove(self)
        print("WebSocket closed")

    @gen.coroutine
    def feed(self):
        conn = yield r.connect(host="localhost", port=28015)
        feed = yield r.db("myops2").table("resources").changes().run(conn)
        while (yield feed.fetch_next()):
            change = yield feed.next()
            self.write_message(json.dumps(change, ensure_ascii = False).encode('utf8'))
            print(change)
