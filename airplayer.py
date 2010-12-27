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

from xbmc import XBMC
from web import Webserver
import settings
import utils

import signal

class Runner(object):
    
    def __init__(self, port):
        self.port = port
        self.xbmc = None
        self.web = None
        
    def _register_bonjour(self):
        """
        Register our service with bonjour.
        gethostname() often returns <hostname>.local, remove that.
        """
        hostname = gethostname()
        hostname = utils.clean_hostname(hostname)
        thread.start_new_thread(bonjour.register_service, (hostname, "_airplay._tcp", self.port,))
        
    def _connect_to_xbmc(self):
        username = None
        password = None

        if getattr(settings, 'XBMC_USERNAME', None) and settings.XBMC_USERNAME:
            username = settings.XBMC_USERNAME

        if getattr(settings, 'XBMC_PASSWORD', None) and settings.XBMC_PASSWORD:
            password = settings.XBMC_PASSWORD

        self.xbmc = XBMC(settings.XBMC_HOST, settings.XBMC_PORT, username, password)
        
    def _start_web(self):
        self.web = Webserver(self.port)
        self.web.xbmc = self.xbmc
        self.web.start()
        
    def run(self):
        self._register_bonjour()
        self._connect_to_xbmc()
        
        self.xbmc.notify_started()
        self._start_web()
    
    def receive_signal(self, signum, stack):
        self.web.stop()
        self.xbmc.stop_playing()

def main():    
    runner = Runner(6002)
    signal.signal(signal.SIGTERM, runner.receive_signal)
    
    try:
        runner.run()
    except Exception, e:    
        print 'Unable to connect to XBMC at %s' % runner.xbmc._host_string()
        print e
        sys.exit(1)

if __name__ == '__main__':
    main()
