from tornado import web

from myops2.web import templates

class Index(web.RequestHandler):
    def get(self):
        self.render(templates + "/index.html")