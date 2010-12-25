import urllib2
import urllib
import os
import base64

import jsonrpclib
from logger import logger

class XBMC(object):
    
    def __init__(self, host, port, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        self._jsonrpc = jsonrpclib.Server(self._jsonrpc_connection_string())
    
    def _jsonrpc_connection_string(self):
        host_string = self._host_string()
        
        if self.username and self.password:
            host_string = '%s:%s@%s' % (self.username, self.password, host_string)
            
        return 'http://%s/jsonrpc' % host_string    
        
    def _host_string(self):
        return '%s:%d' % (self.host, self.port)
        
    def _http_request(self, req):
        if self.username and self.password:
            base64string = base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)

        return urllib2.urlopen(req)

    def _http_api_request(self, command):
        command = urllib.quote(command)
        url = 'http://%s/xbmcCmds/xbmcHttp?command=%s' % (self._host_string(), command)

        req = urllib2.Request(url)
        return self._http_request(req)
        
    def _jsonrpc_api_request(self, method, *args):
        """
        Wrap calls to the json-rpc proxy to conveniently handle exceptions.
        @return response, exception
        """
        response = None
        exception = None
        
        try:    
            response = self._jsonrpc._request(method, args)
        except jsonrpclib.ProtocolError, e:
            """
            Protocol errors usually means a method could not be executed because
            for example a seek is requested when there's no movie playing.
            """
            logger.info('Caught protocol error %s', e)
            exception = e
        except Exception, e:
            exception = e
            
        return response, exception
        
    def _send_notification(self, title, message):
        self._http_api_request('ExecBuiltIn(Notification(%s, %s))' % (title, message))
        
    def stop_playing(self):
        self._http_api_request('stop')
        
    def show_picture(self, path):
        logger.debug('Showing picture: %s', path)
        dir = os.path.dirname(path)
        
        #self._jsonrpc.xbmc.startslideshow(dir)
        self._http_api_request('PlaySlideshow(%s)' % dir)
        
    def play_movie(self, url):
        self._http_api_request('PlayFile(%s)' % url)

    def notify(self):
        self._send_notification('Airplayer', 'Airplayer started')
        
    def get_player_state(self, player):
        return self._jsonrpc_api_request('%s.state' % player)
        
    def _pause(self):
        self._http_api_request('Pause')       

    def pause(self):
        response, error = self.get_player_state('videoplayer')
        
        if response and not response['paused']:
            self._pause()
    
    def _play(self):
        """
        XBMC doesn't have a real play command, just play/pause.
        This method is purely for code readability.
        """
        self._pause()        
        
    def play(self):
        """
        Airplay sometimes sends a play command twice and since XBMC
        does not offer a seperate play and pause command we'll have
        to check the current player state and choose an action
        accordingly.
        
        If an error is returned there's not currently playing any
        media, so we can send the play command.
        
        If there's a response and the videoplayer is currently playing
        we can also send the play command.
        """
        response, error = self.get_player_state('videoplayer')
        
        if error or response and response['paused']:
            self._play()
        
    def get_player_position(self):
        #response = self._jsonrpc.videoplayer.gettime()
        response, error = self._jsonrpc_api_request('videoplayer.gettime')
        
        if not error:
            if 'time' in response:
                return int(response['time']), int(response['total'])

        return 0, 0

    def set_player_position(self, position):
        #self._jsonrpc.videoplayer.seektime(position)
        self._jsonrpc_api_request('videoplayer.seektime', position)