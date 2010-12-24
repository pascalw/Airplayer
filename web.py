import tornado.httpserver
import tornado.ioloop
import tornado.web

import tempfile
import shutil
import time

from logger import logger
import utils

class BaseHandler(tornado.web.RequestHandler):

    def initialize(self, xbmc):
        self._xbmc = xbmc  

    def prepare(self):
        print '%s %s' % (self.request.method, self.request.uri)

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
            
        self._xbmc.play_movie(info['Content-Location'])
    
        self._send_ok()
        self.request.finish()

class ScrubHandler(BaseHandler):        

    def get(self):
        position, duration = self._xbmc.get_player_position()
        body = 'duration: %d\nposition: %d\n' % (duration, position)
        self.write(body)

        #logger.debug('Scrub GET %s', body)
 
    @tornado.web.asynchronous    
    def post(self):
        self._send_ok()
        self.request.finish()
    
        if 'position' in self.request.arguments:
            self._xbmc.set_player_position(int(float(self.request.arguments['position'][0])))
        #logger.debug('Scrub POST %s', self.request.arguments['position'])
    
class RateHandler(BaseHandler):

    def post(self):
        self._send_ok()
            
        #if 'value' in self.request.arguments:           
        #    xbmc.pause()

class PhotoHandler(BaseHandler):        

    def put(self):        
        self._send_ok()
    
        if self.request.body:
            utils.clear_folder(Webserver.TMP_DIR)
            path = '%s/picture%d.jpg' % (Webserver.TMP_DIR, int(time.time()))

            f = open(path, 'w')
            f.write(self.request.body)
            f.close()
        
            self._xbmc.show_picture(path)
    
class StopHandler(BaseHandler):

    @tornado.web.asynchronous
    def post(self):
        self._xbmc.stop_playing()
        self._send_ok()
        self.request.finish()

class Webserver(object):
    
    TMP_DIR = None
    
    def __init__(self, port):
        self.xbmc = None
        self.http_server = None
        self.port = port
        
        Webserver.TMP_DIR = tempfile.mkdtemp()
        logger.debug('TEMP DIR: %s', Webserver.TMP_DIR)
    
    def start(self):        
        application = tornado.web.Application([
            (r"/reverse", ReverseHandler, dict(xbmc=self.xbmc)),
            (r"/play", PlayHandler, dict(xbmc=self.xbmc)),
            (r"/scrub", ScrubHandler, dict(xbmc=self.xbmc)),
            (r"/rate", RateHandler, dict(xbmc=self.xbmc)),
            (r"/photo", PhotoHandler, dict(xbmc=self.xbmc)),
            (r"/stop", StopHandler, dict(xbmc=self.xbmc)),
        ])

        self.http_server = tornado.httpserver.HTTPServer(application)
        self.http_server.listen(self.port)

        try:
            tornado.ioloop.IOLoop.instance().start()
        except:
            pass
        finally:
            logger.debug('Cleaning up')
            shutil.rmtree(Webserver.TMP_DIR)
        
    def stop(self):
        self.http_server.stop()      