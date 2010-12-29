#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Pascal Widdershoven on 2010-12-19.
Copyright (c) 2010 P. Widdershoven. All rights reserved.
"""

import sys
import thread
import bonjour
from socket import gethostname

from web import Webserver
import settings
import utils

import signal

class Runner(object):
    
    def __init__(self, port):
        self.port = port
        self.media_backend = None
        self.web = None
        
    def _register_bonjour(self):
        """
        Register our service with bonjour.
        """
        if getattr(settings, 'AIRPLAY_HOSTNAME', None):
            hostname = settings.AIRPLAY_HOSTNAME
        else:    
            hostname = gethostname()
            """
            gethostname() often returns <hostname>.local, remove that.
            """
            hostname = utils.clean_hostname(hostname)
            
            if not hostname:
                hostname = 'Airplayer'
        
        thread.start_new_thread(bonjour.register_service, (hostname, "_airplay._tcp", self.port,))
        
    def _connect_to_media_backend(self):        
        backend_module = '%s_media_backend' % settings.MEDIA_BACKEND
        backend_class = '%sMediaBackend' % settings.MEDIA_BACKEND
        
        try:        
            mod = __import__('mediabackends.%s' % backend_module, fromlist=[backend_module])
        except ImportError:
            raise Exception('Invalid media backend specified: %s' % settings.MEDIA_BACKEND)
                
        backend_cls = getattr(mod, backend_class)
        
        username = getattr(settings, 'MEDIA_BACKEND_USERNAME', None)
        password = getattr(settings, 'MEDIA_BACKEND_PASSWORD', None)

        self.media_backend = backend_cls(settings.MEDIA_BACKEND_HOST, settings.MEDIA_BACKEND_PORT, username, password)
        
    def _start_web(self):
        self.web = Webserver(self.port)
        self.web.media_backend = self.media_backend
        self.web.start()
        
    def run(self):
        self._register_bonjour()
        self._connect_to_media_backend()
        
        self.media_backend.notify_started()
        self._start_web()
    
    def receive_signal(self, signum, stack):
        self.web.stop()
        self.media_backend.stop_playing()

def main():    
    runner = Runner(6002)
    signal.signal(signal.SIGTERM, runner.receive_signal)
    
    try:
        runner.run()
    except Exception, e:
        print 'Error: %s' % e
        sys.exit(1)

if __name__ == '__main__':
    main()
