import urllib2
import urllib
import time
import thread
import tempfile
import shutil
import os
import string
import xml.dom.minidom

from base_media_backend import BaseMediaBackend

class VLCMediaBackend(BaseMediaBackend):
    """
    The VLC media backend uses the VLC HTTP API to connect to VLC. This requires that
    the VLC web interface be activated, which can be done in either of the following ways:

    1) Run "vlc -I http" from the command line
    2) Run vlc and then select View->Add Interface->Web Interface
    """

    def __init__(self, host, port, username=None, password=None):
        super(VLCMediaBackend, self).__init__(host, port, username, password)

        self._TMP_DIR = tempfile.mkdtemp()

        self.log.debug('TEMP DIR: %s', self._TMP_DIR)

    def _http_api_request(self, command):
        """
        Send a request to the VLC web interface.
        @return string status.xml page
        """

        url = 'http://%s/requests/status.xml?%s' % (self.host_string(), command)

        req = urllib2.Request(url)
        return self._http_request(req)

    def _playlist_empty(self):
        """
        Empty the VLC playlist.
        """
        self._http_api_request('command=pl_empty')

    def _playlist_add(self, url):
        """
        Add url to the VLC playlist.
        @param url the address of the media file to add
        """
        
        url = urllib.quote(url)
        self._http_api_request('command=in_play&input=%s' % url)

    def _get_xml_nodes_data(self, *nodesNames):
        """
        Get the data out of specific xml nodes.
        @param nodesNames any number of dot-delimited xml nodes, i.e. root.time, root.length  These are presumed to be unique, or the first one is obtained (first in no particular order)
        @return list data from the requested xml nodes
        """
        
        status = self._http_api_request('')
        values = []

        if status:
            xmlStatus = xml.dom.minidom.parseString(status)

            for name in nodesNames:
                n = xmlStatus
                try:
                    # Iterate down the tree until we get to the node whose data we want
                    for node in string.split(name, '.'):
                        n = n.getElementsByTagName(node)[0]
                    values.append(n.childNodes[0].data)
                except Exception:
                    # The node doesn't exist
                    values.append('')
        return values

    def _set_start_position(self, position_percentage):
        for i in range(3):
            current_position, length = self.get_player_position()

            if length == 0:
                time.sleep(1)
                continue
            
            self.set_player_position_percentage(position_percentage)
            desired_position = int(position_percentage * float(length) / 100.)
            current_position, length = self.get_player_position()

            if current_position not in range(desired_position - 3, desired_position + 4):
                # We don't care if the player is within a couple seconds of the desired position
                self.log.debug('Setting start position failed')
                time.sleep(1)
                continue

            self.log.debug('Setting start position succeeded')    
            return

        self.log.warning('Failed to set start position')

    def cleanup(self):
        """
        Called when airplayer is about to shutdown.
        """
        self.stop_playing()
        self._playlist_empty()
        shutil.rmtree(self._TMP_DIR)                          
        
    def stop_playing(self):
        """
        Stop playing media.
        """
        self._http_api_request('command=pl_stop')
        
    def show_picture(self, data):
        """
        Show a picture.

        Cannot do this in VLC, so we'll just pass here.

        @param data raw picture data.
        """
        pass
        
    def play_movie(self, url):
        """
        Play a movie from the given location.
        @param url the address of the media file to add
        """

        self._playlist_empty()
        self._playlist_add(url)

    def notify_started(self):
        """
        I don't believe there is a way to display a message to the user in VLC, so we are just going to print a message to the airplayer terminal instead saying that this backend has been loaded.
        """
        print "Started connection to VLC"
        
    def get_state(self):
        """
        Return the current state (playing, paused) of the player.
        @return string current state
        """
        return str(self._get_xml_nodes_data('root.state')[0])

    def _pause(self):
        """
        Play/Pause media playback.
        """
        self._http_api_request('command=pl_pause')
        
    def pause(self):
        """
        Pause media playback.
        VLC doesn't have a seperate play and pause command so we'll
        have to check if there's currently playing any media.
        """
        state = self.get_state()

        if state != 'paused':
            self._pause()
        
    def _play(self):
        """
        VLC doesn't have a real play command, just play/pause.
        This method is purely for code readability.
        """
        self._pause()

    def play(self):
        """
        Airplay sometimes sends a play command twice and since VLC
        does not offer a seperate play and pause command we'll have
        to check the current player state and choose an action
        accordingly.
        """
        state = self.get_state()

        if state == 'paused':
            self._play()
        
    def get_player_position(self):
        """
        Get the current videoplayer position.
        @returns int current position, int total length
        """
        time, length = self._get_xml_nodes_data('root.time', 'root.length')
        return int(time), int(length)
        

    def set_player_position(self, position):
        """
        Set the current videoplayer position.
        @param position integer in seconds
        """
        self._http_api_request('command=seek&val=%s' % position)

    def set_player_position_percentage(self, percentage_position):
        """
        Set current videoplayer position, in percentage.
        @param percentage_position float
        """
        
        length = self._get_xml_nodes_data('root.length')[0]
        newPosition = int(percentage_position * float(length) / 100.)
        self.set_player_position(newPosition)

    def set_start_position(self, percentage_position):
        """
        It can take a few seconds before VLC starts playing the movie
        and accepts seeking, so we'll wait a bit before sending this command.
        This is a bit dirty, but it's the best I could come up with. 
        @param percentage_position float
        """
        if percentage_position:
            thread.start_new_thread(self._set_start_position, (percentage_position,))

