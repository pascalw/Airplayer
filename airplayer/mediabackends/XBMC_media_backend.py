import urllib2
import urllib
import time
import thread
import tempfile
import shutil
import os

import lib.jsonrpclib as jsonrpclib
import utils

from base_media_backend import BaseMediaBackend

class XBMCMediaBackend(BaseMediaBackend):
    """
    The XBMC media backend uses a hybride Web_Server_HTTP_API / JSON-RPC API approach,
    since the Web_Server_HTTP_API is deprecated from XBMC Dharma (current stable).
    
    However, not all required methods are exposed through the JSON-RPC API, so in that
    cases the old HTTP API is used. In the future when the JSON-RPC is extended to expose
    all required methods, the HTTP API will not be used anymore.
    """
    
    def __init__(self, host, port, username=None, password=None):
        super(XBMCMediaBackend, self).__init__(host, port, username, password)
        
        self._last_wakeup = None
        self._jsonrpc = jsonrpclib.Server(self._jsonrpc_connection_string())
        self._TMP_DIR = tempfile.mkdtemp()
        
        self.log.debug('TEMP DIR: %s', self._TMP_DIR)
    
    def _jsonrpc_connection_string(self):
        host_string = self.host_string()
        
        if self._username and self._password:
            """
            Unfortunately there's no other way to provide authentication credentials
            to jsonrpclib but in the url.
            """
            host_string = '%s:%s@%s' % (self._username, self._password, host_string)
            
        return 'http://%s/jsonrpc' % host_string    

    def _http_api_request(self, command):
        """
        Perform a request to the XBMC http api.
        @return raw request result or None in case of error
        """
        self._wake_screen()
        
        command = urllib.quote(command)
        url = 'http://%s/xbmcCmds/xbmcHttp?command=%s' % (self.host_string(), command)

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
            self._wake_screen()    
            response = self._jsonrpc._request(method, args)
        except jsonrpclib.ProtocolError, e:
            """
            Protocol errors usually means a method could not be executed because
            for example a seek is requested when there's no movie playing.
            """
            self.log.debug('Caught protocol error %s', e)
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
                self.log.debug('Setting start position failed: %s', error)
                time.sleep(1)
                continue

            self.log.debug('Setting start position succeeded')    
            return

        self.log.warning('Failed to set start position')
        
    def _wake_screen(self):
        """
        XBMC doesn't seem to wake the screen when the screen is dimmed and a slideshow is started.
        See http://trac.xbmc.org/ticket/10883.
        
        There isn't a real method to wake the screen, so we'll just send a bogus request which does
        nothing, but does wake up the screen.
        
        For performance concerns, we only send this request once every minute.
        """
        now = time.time()
        
        if not self._last_wakeup or now - self._last_wakeup > 60:
            self._last_wakeup = now
            
            self.log.debug('Sending wake event')
            self._http_api_request('sendkey(ACTION_NONE)')
        
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
        filename = 'picture%d.jpg' % int(time.time())
        path = os.path.join(self._TMP_DIR, filename)
        
        """
        write mode 'b' is needed for Windows compatibility, since we're writing a binary file here.
        """
        f = open(path, 'wb')
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
        @returns int current position, int total length
        """
        response, error = self._jsonrpc_api_request('videoplayer.gettime')
        
        if not error:
            if 'time' in response:
                return int(response['time']), int(response['total'])

        return None, None
    
    def set_player_position(self, position):
        """
        Set the current videoplayer position.
        
        @param position integer in seconds
        """
        self._jsonrpc_api_request('videoplayer.seektime', position)
        
    def set_player_position_percentage(self, percentage_position):
        """
        Set current videoplayer position, in percentage.
        
        @param percentage_position float
        """
        return self._jsonrpc_api_request('videoplayer.seekpercentage', percentage_position)
        
    def set_start_position(self, percentage_position):
        """
        It can take a few seconds before XBMC starts playing the movie
        and accepts seeking, so we'll wait a bit before sending this command.
        This is a bit dirty, but it's the best I could come up with.
        
        @param percentage_position float
        """
        if percentage_position:
            thread.start_new_thread(self._set_start_position, (percentage_position,))