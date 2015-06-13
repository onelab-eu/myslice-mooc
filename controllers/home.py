import os
from tornado import web

templates = os.path.realpath(os.path.dirname(__file__) + '/../templates')
static = os.path.realpath(os.path.dirname(__file__) + '/../static')

class Index(web.RequestHandler):
    def get(self):
        self.render(templates + "/index.html")