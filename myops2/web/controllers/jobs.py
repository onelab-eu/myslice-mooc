from tornado import web

from myops2.web import templates

class Log(web.RequestHandler):
    def get(self):
        self.render(templates + "/jobs/log.html")