"""
Set your Media Backend. For now only XBMC is supported, but in the future
this could also be Plex or Boxee for example.
"""
MEDIA_BACKEND = 'XBMC'

MEDIA_BACKEND_HOST = '127.0.0.1'
MEDIA_BACKEND_PORT = 8080

MEDIA_BACKEND_USERNAME = 'username'
MEDIA_BACKEND_PASSWORD = 'password'

"""
This is the name by which Airplayer will identify itself to other Airplay
devices.
Leave this to None for auto-detection, provide a string to override your
default hostname.
Example:
AIRPLAY_HOSTNAME = 'My XBMC player'
"""
AIRPLAY_HOSTNAME = None

"""
Debug mode, set to False to disable debug logging.
"""
DEBUG = True