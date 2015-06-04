import sys, os, json
from rest import Api
from tornado import web, ioloop

class Index(web.RequestHandler):
    def get(self):
        self.render("index.html")



app = web.Application([
    (r'/', Index),
    (r'/api', Api),
])

if __name__ == '__main__':
    app.listen(80)
    ioloop.IOLoop.instance().start()