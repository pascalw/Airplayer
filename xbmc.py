import urllib2
import urllib
import base64
import time
import thread
import tempfile
import shutil

import jsonrpclib
from logger import logger
import utils

class XBMC(object):
        
    def __init__(self, host, port, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        self._jsonrpc = jsonrpclib.Server(self._jsonrpc_connection_string())
        
        self._TMP_DIR = tempfile.mkdtemp()
        logger.debug('TEMP DIR: %s', self._TMP_DIR)
    
    def _jsonrpc_connection_string(self):
        host_string = self._host_string()
        
        if self.username and self.password:
            """
            Unfortunately there's no other way to provide authentication credentials
            to jsonrpclib but in the url.
            """
            host_string = '%s:%s@%s' % (self.username, self.password, host_string)
            
        return 'http://%s/jsonrpc' % host_string    
        
    def _host_string(self):
        """
        Convenience method, get a string with the current host and port.
        @return <host>:<port>
        """
        return '%s:%d' % (self.host, self.port)
        
    def _http_request(self, req):
        """
        Perform a http request andapply HTTP Basic authentication headers,
        if an username and password are supplied in settings.
        """
        if self.username and self.password:
            base64string = base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)

        try:
            return urllib2.urlopen(req).read()
        except urllib2.URLError, e:
            logger.warning("Couldn't connect to XBMC at %s, are you sure it's running?", self._host_string())
            return None    

    def _http_api_request(self, command):
        """
        Perform a request to the XBMC http api.
        Warning, the caller is reponsible for error handling!
        """
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
        """
        Sends a notification to XBMC, this is displayed to the user as a popup.
        """
        self._http_api_request('ExecBuiltIn(Notification(%s, %s))' % (title, message))
        
    def _set_start_position(self, position_percentage):
        for i in range(3):
            response, error = self.set_player_position_percentage(position_percentage)
            if error:
                logger.debug('Setting start position failed: %s', error.reason)
                time.sleep(1)
                continue

            logger.debug('Setting start position succeeded')    
            return

        logger.warning('Failed to set start position')
        
    def cleanup(self):
        shutil.rmtree(self._TMP_DIR)                          
        
    def stop_playing(self):
        """
        Stop playing media.
        """
        self._http_api_request('stop')
        
    def show_picture(self, data):
        """
        Show a picture.
        @param data raw picture data.
        Note I'm using the XBMC PlaySlideshow command here, giving the pictures path as an argument.
        This is a workaround for the fact that calling the XBMC ShowPicture method more than once seems
        to crash XBMC?
        """
        utils.clear_folder(self._TMP_DIR)
        path = '%s/picture%d.jpg' % (self._TMP_DIR, int(time.time()))

        f = open(path, 'w')
        f.write(data)
        f.close()
            
        self._http_api_request('PlaySlideshow(%s)' % self._TMP_DIR)
        
    def play_movie(self, url):
        """
        Play a movie from the given location.
        """
        self._http_api_request('PlayFile(%s)' % url)

    def notify_started(self):
        """
        Notify the user that Airplayer has started.
        """
        self._send_notification('Airplayer', 'Airplayer started')
    
    def get_player_state(self, player):
        """
        Return the current state for the given player. 
        @param player a valid player (e.g. videoplayer, audioplayer etc)
        """
        return self._jsonrpc_api_request('%s.state' % player)
        
    def _pause(self):
        """
        Play/Pause media playback.
        """
        self._http_api_request('Pause')       
        
    def pause(self):
        """
        Pause media playback.
        XBMC doesn't have a seperate play and pause command so we'll
        have to check if there's currently playing any media.
        """
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
        """
        Get the current videoplayer positon.
        @returns dictionary, exception
        """
        response, error = self._jsonrpc_api_request('videoplayer.gettime')
        
        if not error:
            if 'time' in response:
                return int(response['time']), int(response['total'])

        return None, None
    
    def set_player_position(self, position):
        """
        Set the current videoplayer position.
        @param position integer
        """
        self._jsonrpc_api_request('videoplayer.seektime', position)
        
    def set_player_position_percentage(self, percentage_position):
        """
        Set current videoplayer position, in percentage.
        """
        return self._jsonrpc_api_request('videoplayer.seekpercentage', percentage_position)
        
    def set_start_position(self, percentage_position):
        """
        It can take a few seconds before XBMC starts playing the movie
        and accepts seeking, so we'll wait a bit before sending this command.
        This is a bit dirty, but it's the best I could come up with.
        """
        thread.start_new_thread(self._set_start_position, (percentage_position,))        