import logging

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.httputil import HTTPHeaders

log = logging.getLogger('airplayer')

class AirplayProtocolHandler(object):
    
    def __init__(self, port, media_backend):
        self._http_server = None
        self._media_backend = media_backend
        self._port = port
    
    def start(self):
        handler_dict = {
            '/reverse' : AirplayProtocolHandler.ReverseHandler,
            '/play' : AirplayProtocolHandler.PlayHandler,
            '/scrub' : AirplayProtocolHandler.ScrubHandler,
            '/rate' : AirplayProtocolHandler.RateHandler,
            '/photo' : AirplayProtocolHandler.PhotoHandler,
            '/authorize' : AirplayProtocolHandler.AuthorizeHandler,
            '/stop' : AirplayProtocolHandler.StopHandler,
        }
        
        handlers = [(url, handler_dict[url], dict(media_backend=self._media_backend)) for url in handler_dict.keys()] 
        application = tornado.web.Application(handlers)

        self._http_server = tornado.httpserver.HTTPServer(application)
        self._http_server.listen(self._port)

        try:
            tornado.ioloop.IOLoop.instance().start()
        except:
            pass
        finally:
            log.debug('Cleaning up')
            self._media_backend.cleanup()
        
    def stop(self):
        try:
            tornado.ioloop.IOLoop.instance().stop()
            self._http_server.stop()
        except:
            pass
    
    class BaseHandler(tornado.web.RequestHandler):
        """
        Base request handler, all other handler should inherit from this class.

        Provides some logging and media backend assignment.
        """

        def initialize(self, media_backend):
            self._media_backend = media_backend  

        def prepare(self):
            log.debug('%s %s', self.request.method, self.request.uri)

    class ReverseHandler(BaseHandler):
        """
        Handler for /reverse requests.

        The reverse command is the first command sent by Airplay,
        it's a handshake.
        """

        def post(self):
            self.set_status(101)
            self.set_header('Upgrade', 'PTTH/1.0')
            self.set_header('Connection', 'Upgrade')

    class PlayHandler(BaseHandler):
        """
        Handler for /play requests.

        Contains a header like format in the request body which should contain a
        Content-Location and optionally a Start-Position.
        """

        @tornado.web.asynchronous
        def post(self):
            """
            Immediately finish this request, no need for the client to wait for
            backend communication.
            """
            self.finish()

            body = HTTPHeaders.parse(self.request.body)

            if 'Content-Location' in body:
                self._media_backend.play_movie(body['Content-Location'])

                if 'Start-Position' in body:
                    """ 
                    Airplay sends start-position in percentage from 0 to 1.
                    Media backends expect a percentage from 0 to 100.
                    """
                    try:
                        str_pos = body['Start-Position']
                    except ValueError:
                        log.warning('Invalid start-position supplied: ', str_pos)
                    else:        
                        position_percentage = float(str_pos) * 100
                        self._media_backend.set_start_position(position_percentage)


    class ScrubHandler(BaseHandler):
        """
        Handler for /scrub requests.

        Used to perform seeking (POST request) and to retrieve current player position (GET request).
        """       

        def get(self):
            """
            Will return None, None if no media is playing or an error occures.
            """
            position, duration = self._media_backend.get_player_position()

            """
            Should None values be returned just default to 0 values.
            """
            if not position:
                duration = position = 0

            body = 'duration: %f\r\nposition: %f\r\n' % (duration, position)
            self.write(body)

        @tornado.web.asynchronous
        def post(self):
            """
            Immediately finish this request, no need for the client to wait for
            backend communication.
            """
            self.finish()

            if 'position' in self.request.arguments:
                try:
                    str_pos = self.request.arguments['position'][0]
                    position = int(float(str_pos))
                except ValueError:
                    log.warn('Invalid scrub value supplied: ', str_pos)
                else:       
                    self._media_backend.set_player_position(position)

    class RateHandler(BaseHandler):    
        """
        Handler for /rate requests.

        The rate command is used to play/pause media.
        A value argument should be supplied which indicates media should be played or paused.

        0.000000 => pause
        1.000000 => play
        """

        @tornado.web.asynchronous
        def post(self): 
            """
            Immediately finish this request, no need for the client to wait for
            backend communication.
            """
            self.finish()

            if 'value' in self.request.arguments:
                play = bool(float(self.request.arguments['value'][0]))

                if play:
                    self._media_backend.play()
                else:
                    self._media_backend.pause()    

    class PhotoHandler(BaseHandler):   
        """
        Handler for /photo requests.

        RAW JPEG data is contained in the request body.
        """     

        @tornado.web.asynchronous
        def put(self):           
            """
            Immediately finish this request, no need for the client to wait for
            backend communication.
            """
            self.finish()

            if self.request.body:        
                self._media_backend.show_picture(self.request.body)

    class AuthorizeHandler(BaseHandler):
        """
        Handler for /authorize requests.

        This is used to handle DRM authorization.
        We currently don't support DRM protected media.
        """

        def prepare(self):
            log.warning('Trying to play DRM protected, this is currently unsupported.')
            log.debug('Got an authorize %s request', self.request.method)
            log.debug('Authorize request info: %s %s %s', self.request.headers, self.request.arguments, self.request.body)

        def get(self):
            pass

        def post(self):
            pass    

    class StopHandler(BaseHandler):
        """
        Handler for /stop requests.

        Sent when media playback should be stopped.
        """

        def post(self):
            self._media_backend.stop_playing()