class BaseMediaBackend(object):
    
    def __init__(self, host, port, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
                
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
        @returns dictionary, exception
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