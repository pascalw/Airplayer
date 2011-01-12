#!/usr/bin/env python
# encoding: utf-8
"""
airplayer.py

Created by Pascal Widdershoven on 2010-12-19.
Copyright (c) 2010 P. Widdershoven. All rights reserved.
"""

import sys
import thread
from socket import gethostname
import signal
from optparse import OptionParser
import logging
import os

import bonjour
from protocol_handler import AirplayProtocolHandler
import settings
import utils
from pidfile import Pidfile

class Application(object):
    
    def __init__(self, port):
        self._port = port
        self._pidfile = None
        self._media_backend = None
        self._protocol_handler = None
        self._opts = None
        self._args = None
        
        self.log = None
        
    def _setup_path(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))  
        
    def _configure_logging(self):
        """
        Configure logging.
        When no logfile argument is given we log to stdout.
        """
        self.log = logging.getLogger('airplayer')

        fmt = r"%(asctime)s [%(levelname)s] %(message)s"
        datefmt = r"%Y-%m-%d %H:%M:%S"

        if self._opts.logfile:
            handler = logging.FileHandler(self._opts.logfile)
        else:
            handler = logging.StreamHandler()

        if getattr(settings, 'DEBUG', None) and settings.DEBUG:
            loglevel = logging.DEBUG
        else:
            loglevel = logging.WARNING
            
        self.log.setLevel(loglevel)
        handler.setFormatter(logging.Formatter(fmt, datefmt))
        self.log.addHandler(handler)
        
    def _parse_opts(self):
        parser = OptionParser(usage='usage: %prog [options] filename')
        
        parser.add_option('-d', '--daemon', 
            action='store_true', 
            dest='daemon', 
            default=False,
            help='run Airplayer as a daemon in the background'
        )
        
        parser.add_option('-p', '--pidfile', 
            action='store',
            type='string', 
            dest='pidfile',
            default=None,
            help='path for the PID file'
        )
        
        parser.add_option('-l', '--logfile', 
            action='store',
            type='string', 
            dest='logfile', 
            default=None,
            help='path for the PID file'
        )
        
        (self._opts, self._args) = parser.parse_args()
        
        file_opts = ['logfile', 'pidfile']
        for opt in file_opts:
            """
            Expand user variables for all options containing a file path
            """
            value = getattr(self._opts, opt, None)
            
            if value:
                setattr(self._opts, opt, os.path.expanduser(value))                        
        
        if self._opts.daemon:
            if not self._opts.pidfile or not self._opts.logfile:
                print "It's required to specify a logfile and a pidfile when running in daemon mode.\n"
                parser.print_help()
                sys.exit(1)
                
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
        
        thread.start_new_thread(bonjour.register_service, (hostname, "_airplay._tcp", self._port,))
        
    def _register_media_backend(self):
        """
        Backends follow the following naming convention:
        
        Backend module should be named <backend_name>_media_backend and should contain
        a class named <backend_name>MediaBackend which inherits from the BaseMediaBackend.
        """        
        backend_module = '%s_media_backend' % settings.MEDIA_BACKEND
        backend_class = '%sMediaBackend' % settings.MEDIA_BACKEND
                
        try:        
            mod = __import__('mediabackends.%s' % backend_module, fromlist=[backend_module])
        except ImportError, e:
            print e
            raise Exception('Invalid media backend specified: %s' % settings.MEDIA_BACKEND)
                
        backend_cls = getattr(mod, backend_class)
        
        username = getattr(settings, 'MEDIA_BACKEND_USERNAME', None)
        password = getattr(settings, 'MEDIA_BACKEND_PASSWORD', None)

        self._media_backend = backend_cls(settings.MEDIA_BACKEND_HOST, settings.MEDIA_BACKEND_PORT, username, password)
        
    def _init_signals(self):
        """
        Setup kill signal handlers.
        """
        signals = ['TERM', 'HUP', 'QUIT', 'INT']

        for signame in signals:
            """
            SIGHUP and SIGQUIT are not available on Windows, so just don't register a handler for them
            if they don't exist.
            """
            sig = getattr(signal, 'SIG%s' % signame, None)
            
            if sig:
                signal.signal(sig, self.receive_signal)    
        
    def _start_protocol_handler(self):
        """
        Start the webserver and connect our media backend.
        """
        self._protocol_handler = AirplayProtocolHandler(self._port, self._media_backend)
        self._protocol_handler.start()
                
    def run(self):
        """
        Run the application.
        Perform some bootstrapping, fork/daemonize if necessary.
        """
        self._parse_opts()
        self._setup_path()
                
        if self._opts.daemon:
            utils.daemonize()
            
            pid = os.getpid()
            self._pidfile = Pidfile(self._opts.pidfile)
            self._pidfile.create(pid)

        self._init_signals()
        self._configure_logging()
        self.log.info('Starting Airplayer')

        self._register_bonjour()
        self._register_media_backend()

        self._media_backend.notify_started()
        self._start_protocol_handler()
    
    def shutdown(self):
        """
        Called on application shutdown.
        
        Stop the webserver and stop the media backend.
        """
        self._protocol_handler.stop()
        self._media_backend.stop_playing()
        
        if self._opts.daemon:
            self._pidfile.unlink()
            
    def receive_signal(self, signum, stack):
        self.shutdown()    

def main():
    app = Application(6002)
    
    try:
        app.run()
    except Exception, e:
        raise e
        sys.exit(1)

if __name__ == '__main__':
    main()
