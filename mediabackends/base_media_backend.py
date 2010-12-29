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
        raise TypeError('Abstract method called, implement in subclass.')
        
    def stop_playing(self):
        """
        Stop playing media.
        """
        raise TypeError('Abstract method called, implement in subclass.')
        
    def show_picture(self, data):
        """
        Show a picture.
        @param data raw picture data.
        """
        raise TypeError('Abstract method called, implement in subclass.')
        
    def play_movie(self, url):
        """
        Play a movie from the given location.
        """
        raise TypeError('Abstract method called, implement in subclass.')

    def notify_started(self):
        """
        Notify the user that Airplayer has started.
        """
        raise TypeError('Abstract method called, implement in subclass.')
        
    def pause(self):
        """
        Pause media playback.
        """
        raise TypeError('Abstract method called, implement in subclass.')
    
    def play(self):
        """
        Play media
        """
        raise TypeError('Abstract method called, implement in subclass.')
        
    def get_player_position(self):
        """
        Get the current videoplayer positon.
        @returns dictionary, exception
        """
        raise TypeError('Abstract method called, implement in subclass.')
    
    def set_player_position(self, position):
        """
        Set the current videoplayer position.
        @param position integer
        """
        raise TypeError('Abstract method called, implement in subclass.')
        
    def set_player_position_percentage(self, percentage_position):
        """
        Set current videoplayer position, in percentage.
        """
        raise TypeError('Abstract method called, implement in subclass.')
        
    def set_start_position(self, percentage_position):
        """
        Play media from the given location
        """
        raise TypeError('Abstract method called, implement in subclass.')