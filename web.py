import tornado.httpserver
import tornado.ioloop
import tornado.web

import tempfile
import time

import xbmc

TMP_DIR = tempfile.mkdtemp()

class BaseHandler(tornado.web.RequestHandler):
    
    def _send_ok(self):
        self.request.write("HTTP/1.1 200 OK\n"
        					"Content-Length: 0\n\n")

class ReverseHandler(BaseHandler):
    
    @tornado.web.asynchronous
    def post(self):
        self.request.write("HTTP/1.1 101 Switching Protocols\n"
        							"Upgrade: PTTH/1.0\n"
        							"Connection: Upgrade\n\n")
        self.request.finish()
        
class PlayHandler(BaseHandler):
    
    @tornado.web.asynchronous
    def post(self):
        body = self.request.body
        
        info = {}
        
        for line in body.splitlines():
            if line:
                name, value = line.split(":", 1)
                info[name] = value
                
        xbmc.play_movie(info['Content-Location'])
        
        self._send_ok()
        self.request.finish()

class ScrubHandler(BaseHandler):        

    def get(self):
        pass
     
    @tornado.web.asynchronous    
    def post(self):
        self._send_ok()
        self.request.finish()
        
class RateHandler(BaseHandler):        

    def post(self):
        self._send_ok()

class PhotoHandler(BaseHandler):        

    def put(self):        
        self._send_ok()
        
        if self.request.body:
            path = '%s/picture%d.jpg' % (TMP_DIR, int(time.time()))

            f = open(path, 'w')
            f.write(self.request.body)
            f.close()
            
            xbmc.show_picture(path)
        
class StopHandler(BaseHandler):
    
    @tornado.web.asynchronous
    def post(self):
        xbmc.stop()
        self._send_ok()
        self.request.finish()

application = tornado.web.Application([
    (r"/reverse", ReverseHandler),
    (r"/play", PlayHandler),
    (r"/scrub", ScrubHandler),
    (r"/rate", RateHandler),
    (r"/photo", PhotoHandler),
    (r"/stop", StopHandler),
])

def start(port):
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()