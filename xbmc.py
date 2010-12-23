import urllib2
import urllib
import settings
import os

def _request(command):
    command = urllib.quote(command)
    urllib2.urlopen('http://%s:%d/xbmcCmds/xbmcHttp?command=%s' % (settings.XBMC_HOST, settings.XBMC_PORT, command))

def stop():
    _request('stop')

def show_picture(path):    
    _request('PlaySlideshow(%s)' % os.path.dirname(path))
    os.remove(path)
    
def play_movie(url):
    _request('PlayFile(%s)' % url)
    
def notify():
    _request('ExecBuiltIn(Notification(Airplayer, Airplayer started))')    