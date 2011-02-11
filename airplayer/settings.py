"""
Port used by Airplayer.
You should only need to change this in case port 6002 is already
in use on your machine by other software.
"""
AIRPLAYER_PORT = 6002

"""
Set your media backend.
Supported media backends are XBMC, Plex and Boxee.
"""
MEDIA_BACKEND = 'XBMC'

"""
Default ports:
XBMC: 8080
Plex: 3000
Boxee: 8800
"""
MEDIA_BACKEND_HOST = '127.0.0.1'
MEDIA_BACKEND_PORT = 8080

"""
If your media backend doesn't require authentication,
set this options to None.

Example:
MEDIA_BACKEND_USERNAME = None
MEDIA_BACKEND_PASSWORD = None
"""
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
DEBUG = False