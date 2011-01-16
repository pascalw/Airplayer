import time
import utils

from XBMC_media_backend import XBMCMediaBackend

class PlexMediaBackend(XBMCMediaBackend):
    
    class InvalidApiResponseFormatException(Exception):
        pass
    
    _NOTHING_PLAYING = '[Nothing Playing]'
    
    def _http_api_request(self, command):
        response = super(PlexMediaBackend, self)._http_api_request(command)
        
        try:
            return self._parse_http_api_response(response)
        except PlexMediaBackend.InvalidApiResponseFormatException:
            """
            The API result was returned in an unexpected format,
            try to set the response format, and retry the request.
            """ 
            self._init_http_api()
            response = super(PlexMediaBackend, self)._http_api_request(command)
            return self._parse_http_api_response(response)
        
    def _init_http_api(self):
        """
        Set the responseformat so we can conveniently parse the result
        """
        response = self._http_api_request('SetResponseFormat(webheader;false;webfooter;false;opentag;)')
        
        if response['error']:
            raise Exception('Could not set HTTP API response format')    
    
    def _parse_http_api_response(self, response):
        """
        Parse http api responses.
        We except the following response format:
            - One or more lines with key/value pairs
            OR
            - A single line with a single string value (like 'OK')
        """
        result = { 'error' : False }
        
        if not response:
            result['error'] = True
            return result
        
        lines = response.splitlines()
        
        for line in lines:
            if not line:
                """
                Sometimes responses contain empty lines, ignore them
                """
                continue
                
            try:
                key, value = line.split(':', 1)
            except ValueError:
                if '<html>' in line:
                    """
                    The response format is not set yet.
                    """
                    raise PlexMediaBackend.InvalidApiResponseFormatException()
                
                if len(lines) == 1:
                    """
                    The response only contained a single line, with a single value.
                    Wrap it in a response key.
                    """
                    result['response'] = lines[0]
                    return result
                
                """
                The response is invalid, bail out.
                """
                raise Exception('Invalid response item: ', line)    
            
            result[key] = value
        
        if 'Error' in result:
            result['error'] = True
            
        return result
        
    def _set_start_position(self, position_percentage):
        """
        Run in thread.
        See set_start_position in BaseMediaBackend
        
        Max retries is 5, Plex seems to wait longer before media is played
        due to buffering.
        """
        for i in range(5):
            response = self.set_player_position_percentage(position_percentage)
            if 'error' in response and response['error']:
                self.log.debug('Setting start position failed: %s', response)
                time.sleep(1)
                continue

            self.log.debug('Setting start position succeeded')    
            return

        self.log.warning('Failed to set start position')
        
    def _is_playing(self):
        """
        Determine if Plex is currently playing any media.
        
        Playing:
        A file is loaded and PlayStatus != Paused
        
        Not playing:
        No file is loaded, or a file is loaded and PlayStatus == Paused
        """
        response = self.get_player_state()
        
        if response['error']:
            return False
            
        if response['Filename'] == self._NOTHING_PLAYING:
            return False
                        
        return response['PlayStatus'] != 'Paused'
    
    def get_player_state(self):
        """
        Get information about the currently playing media.
        """
        return self._http_api_request('GetCurrentlyPlaying()')
        
    def pause(self):
        """
        Pause media playback.
        Plex doesn't have a seperate play and pause command so we'll
        have to check if there's currently playing any media.
        """
        
        if self._is_playing():
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
        if not self._is_playing():
            self._play()
        
    def get_player_position(self):
        """
        Get the current videoplayer positon.
        @returns int current position, int total length
        """
        response = self.get_player_state()
        
        if not response['error'] and 'Duration' in response:
            total_str = response['Duration']
            time_str = response['Time']
            
            if total_str and time_str:
                total = utils.duration_to_seconds(total_str)
                time = utils.duration_to_seconds(time_str)
            
                return time, total
            
        return None, None    
    
    def set_player_position(self, position):
        """
        Set the current videoplayer position.
        
        Plex doesn't support seeking in seconds, so calculate a percentage
        for the given position first.
        
        @param position integer in seconds
        """
        
        time, total = self.get_player_position()
        
        if total:
            percentage = float(position) / float(total) * 100
            self.log.debug('Position: %d total: %d percentage: %f', position, total, percentage)
            
            self.set_player_position_percentage(percentage)
        
    def set_player_position_percentage(self, percentage_position):
        """
        Set current videoplayer position, in percentage.
        
        @param percentage_position float
        """
        return self._http_api_request('SeekPercentage(%f)' % percentage_position)