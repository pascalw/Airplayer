import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.httputil import HTTPHeaders

from logger import logger

class BaseHandler(tornado.web.RequestHandler):

    def initialize(self, xbmc):
        self._xbmc = xbmc  

    def prepare(self):
        print '%s %s' % (self.request.method, self.request.uri)

class ReverseHandler(BaseHandler):
    """
    The reverse command is the first command sent by Airplay,
    it's a handshake.
    """

    @tornado.web.asynchronous
    def post(self):
        self.request.write('HTTP/1.1 101 Switching Protocols\n'
        							'Upgrade: PTTH/1.0\n'
        							'Connection: Upgrade\n\n')
    
class PlayHandler(BaseHandler):

    @tornado.web.asynchronous
    def post(self):
        self.finish()
        
        body = self.request.body
        info = HTTPHeaders.parse(body)
        
        if 'Content-Location' in info:
            self._xbmc.play_movie(info['Content-Location'])
            
            if 'Start-Position' in info:
                """ 
                Airplay sends start-position in percentage from 0 to 1.
                XBMC expects a percentage from 0 to 100.
                """
                position_percentage = float(info['Start-Position']) * 100
                self._xbmc.set_start_position(position_percentage)
                            

class ScrubHandler(BaseHandler):        

    @tornado.web.asynchronous
    def get(self):
        position, duration = self._xbmc.get_player_position()
        
        if not position:
            duration = position = 0
            
        body = 'duration: %f\r\nposition: %f\r\n' % (duration, position)
        
        self.write(body)
        self.finish()
 
    def post(self):    
        if 'position' in self.request.arguments:
            self._xbmc.set_player_position(int(float(self.request.arguments['position'][0])))
    
class RateHandler(BaseHandler):    
    """
    The rate command is used to play/pause media.
    """

    def post(self):            
        if 'value' in self.request.arguments:
            play = bool(float(self.request.arguments['value'][0]))
            
            if play:
                self._xbmc.play()
            else:
                self._xbmc.pause()    

class PhotoHandler(BaseHandler):        

    def put(self):            
        if self.request.body:        
            self._xbmc.show_picture(self.request.body)
            
class AuthorizeHandler(BaseHandler):
    
    def get(self):
        logger.debug('Got an authorize GET request')
        logger.debug('Authorize request info: %s %s %s', self.request.headers, self.request.arguments, self.request.body)
    
    def post(self):
        logger.debug('Got an authorize POST request')
        logger.debug('Authorize request info: %s %s %s', self.request.headers, self.request.arguments, self.request.body)
    
class StopHandler(BaseHandler):

    def post(self):
        self._xbmc.stop_playing()

class Webserver(object):
    
    def __init__(self, port):
        self.xbmc = None
        self.http_server = None
        self.port = port
    
    def start(self):        
        application = tornado.web.Application([
            (r'/reverse', ReverseHandler, dict(xbmc=self.xbmc)),
            (r'/play', PlayHandler, dict(xbmc=self.xbmc)),
            (r'/scrub', ScrubHandler, dict(xbmc=self.xbmc)),
            (r'/rate', RateHandler, dict(xbmc=self.xbmc)),
            (r'/photo', PhotoHandler, dict(xbmc=self.xbmc)),
            (r'/authorize', AuthorizeHandler, dict(xbmc=self.xbmc)),
            (r'/stop', StopHandler, dict(xbmc=self.xbmc)),
        ])

        self.http_server = tornado.httpserver.HTTPServer(application)
        self.http_server.listen(self.port)

        try:
            tornado.ioloop.IOLoop.instance().start()
        except:
            pass
        finally:
            logger.debug('Cleaning up')
            self.xbmc.cleanup()
        
    def stop(self):
        self.http_server.stop()      