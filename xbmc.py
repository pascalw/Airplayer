import urllib2
import urllib
import settings
import os
import base64

def _request(command):
    command = urllib.quote(command)
    url = 'http://%s:%d/xbmcCmds/xbmcHttp?command=%s' % (settings.XBMC_HOST, settings.XBMC_PORT, command)
    
    req = urllib2.Request(url)
    
    if settings.XBMC_USERNAME:
        base64string = base64.encodestring('%s:%s' % (settings.XBMC_USERNAME, settings.XBMC_PASSWORD))[:-1]
        req.add_header("Authorization", "Basic %s" % base64string)
        
    urllib2.urlopen(req)

def stop():
    _request('stop')

def show_picture(path):    
    _request('PlaySlideshow(%s)' % os.path.dirname(path))
    os.remove(path)
    
def play_movie(url):
    _request('PlayFile(%s)' % url)
    
def notify():
    _request('ExecBuiltIn(Notification(Airplayer, Airplayer started))')    