import logging
import base64
import urllib2

class BaseMediaBackend(object):
    
    def __init__(self, host, port, username=None, password=None):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        
        self.log = logging.getLogger('airplayer')
        
    def _http_request(self, req):
        """
        Perform a http request andapply HTTP Basic authentication headers,
        if an username and password are supplied in settings.
        """
        if self._username and self._password:
            base64string = base64.encodestring('%s:%s' % (self._username, self._password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)

        try:
            return urllib2.urlopen(req).read()
        except urllib2.URLError, e:
            clsname = self.__class__.__name__
            name = clsname.replace('MediaBackend', '')
            
            self.log.warning("Couldn't connect to %s at %s, are you sure it's running?", name, self.host_string())
            return None
    
    def host_string(self):
        """
        Convenience method, get a string with the current host and port.
        @return <host>:<port>
        """
        return '%s:%d' % (self._host, self._port)        
                
    def cleanup(self):
        """
        Called when airplayer is about to shutdown.
        """
        raise NotImplementedError
        
    def stop_playing(self):
        """
        Stop playing media.
        """
        raise NotImplementedError
        
    def show_picture(self, data):
        """
        Show a picture.
        @param data raw picture data.
        """
        raise NotImplementedError
        
    def play_movie(self, url):
        """
        Play a movie from the given location.
        """
        raise NotImplementedError

    def notify_started(self):
        """
        Notify the user that Airplayer has started.
        """
        raise NotImplementedError
        
    def pause(self):
        """
        Pause media playback.
        """
        raise NotImplementedError
    
    def play(self):
        """
        Play media
        """
        raise NotImplementedError
        
    def get_player_position(self):
        """
        Get the current videoplayer positon.
        @returns int current position, int total length
        """
        raise NotImplementedError
        
    def is_playing(self):
        """
        Return wether the backend is currently playing any media.
        
        @returns boolean
        """
        raise NotImplementedError
    
    def set_player_position(self, position):
        """
        Set the current videoplayer position.
        
        @param position integer in seconds
        """
        raise NotImplementedError
        
    def set_player_position_percentage(self, percentage_position):
        """
        Set current videoplayer position, in percentage.
        
        @param percentage_position float
        """
        raise NotImplementedError
        
    def set_start_position(self, percentage_position):
        """
        Play media from the given location
        
        @param percentage_position float
        """
        raise NotImplementedError