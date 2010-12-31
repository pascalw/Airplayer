import logging

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.httputil import HTTPHeaders

log = logging.getLogger('airplayer')

class BaseHandler(tornado.web.RequestHandler):

    def initialize(self, media_backend):
        self._media_backend = media_backend  

    def prepare(self):
        log.info('%s %s', self.request.method, self.request.uri)

class ReverseHandler(BaseHandler):
    """
    The reverse command is the first command sent by Airplay,
    it's a handshake.
    """

    def post(self):
        self.set_status(101)
        self.set_header('Upgrade', 'PTTH/1.0')
        self.set_header('Connection', 'Upgrade')
    
class PlayHandler(BaseHandler):

    @tornado.web.asynchronous
    def post(self):
        self.finish()
        
        body = self.request.body
        info = HTTPHeaders.parse(body)
        
        if 'Content-Location' in info:
            self._media_backend.play_movie(info['Content-Location'])
            
            if 'Start-Position' in info:
                """ 
                Airplay sends start-position in percentage from 0 to 1.
                XBMC expects a percentage from 0 to 100.
                """
                position_percentage = float(info['Start-Position']) * 100
                self._media_backend.set_start_position(position_percentage)
                            

class ScrubHandler(BaseHandler):        

    @tornado.web.asynchronous
    def get(self):
        position, duration = self._media_backend.get_player_position()
        
        if not position:
            duration = position = 0
            
        body = 'duration: %f\r\nposition: %f\r\n' % (duration, position)
        
        self.write(body)
        self.finish()
 
    def post(self):    
        if 'position' in self.request.arguments:
            self._media_backend.set_player_position(int(float(self.request.arguments['position'][0])))
    
class RateHandler(BaseHandler):    
    """
    The rate command is used to play/pause media.
    """

    def post(self):            
        if 'value' in self.request.arguments:
            play = bool(float(self.request.arguments['value'][0]))
            
            if play:
                self._media_backend.play()
            else:
                self._media_backend.pause()    

class PhotoHandler(BaseHandler):        

    def put(self):            
        if self.request.body:        
            self._media_backend.show_picture(self.request.body)
            
class AuthorizeHandler(BaseHandler):
    
    def get(self):
        log.debug('Got an authorize GET request')
        log.debug('Authorize request info: %s %s %s', self.request.headers, self.request.arguments, self.request.body)
    
    def post(self):
        log.debug('Got an authorize POST request')
        log.debug('Authorize request info: %s %s %s', self.request.headers, self.request.arguments, self.request.body)
    
class StopHandler(BaseHandler):

    def post(self):
        self._media_backend.stop_playing()

class Webserver(object):
    
    def __init__(self, port):
        self.media_backend = None
        self.http_server = None
        self.port = port
    
    def start(self):        
        application = tornado.web.Application([
            (r'/reverse', ReverseHandler, dict(media_backend=self.media_backend)),
            (r'/play', PlayHandler, dict(media_backend=self.media_backend)),
            (r'/scrub', ScrubHandler, dict(media_backend=self.media_backend)),
            (r'/rate', RateHandler, dict(media_backend=self.media_backend)),
            (r'/photo', PhotoHandler, dict(media_backend=self.media_backend)),
            (r'/authorize', AuthorizeHandler, dict(media_backend=self.media_backend)),
            (r'/stop', StopHandler, dict(media_backend=self.media_backend)),
        ])

        self.http_server = tornado.httpserver.HTTPServer(application)
        self.http_server.listen(self.port)

        try:
            tornado.ioloop.IOLoop.instance().start()
        except:
            pass
        finally:
            log.debug('Cleaning up')
            self.media_backend.cleanup()
        
    def stop(self):
        try:
            tornado.ioloop.IOLoop.instance().stop()
            self.http_server.stop()
        except:
            pass    
    
