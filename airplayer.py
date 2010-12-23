#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Pascal Widdershoven on 2010-12-19.
Copyright (c) 2010 P. Widdershoven. All rights reserved.
"""

import thread
import bonjour
from socket import gethostname

import xbmc
import web
    
def _register_bonjour(port):
    hostname = gethostname()
    thread.start_new_thread(bonjour.register_service, (hostname, "_airplay._tcp", port,))    

def main():    
    port = 6002
    _register_bonjour(port)
    xbmc.notify()
    
    web.start(port)

if __name__ == '__main__':
    main()