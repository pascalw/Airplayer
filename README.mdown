**WARNING: Airplayer is no longer under active development.
XBMC users can use the built-in Airplay support which is available since XBMC 11 (Eden).**

Airplayer
============
Airplayer is a script to make media playing software Airplay-compatible.
Airplayer features pluggable backends, making it possible to support different
media players.

XBMC, Boxee and Plex are supported through included media backends.
Third party backends for other media players might be available, see [Third Party Media Backends](https://github.com/PascalW/Airplayer/wiki/Third-party-media-backends/).

To create your own media backend
see [this wikipage](https://github.com/PascalW/Airplayer/wiki/Media-backends).

Features
========
Send video and pictures from your iDevice to your Airplay enabled media player. Audio
streaming is currently not supported.

On the iDevice side IOS 4.2 or above is required.

Installing
==========

See INSTALL
    
    
Note
=========
This is pre-release software. It's pretty stable now but it still needs more testing
on different systems and different setups.

If you run into any problems, please don't hesitate to report it.

Known bugs/issues:

* When playing a movie, the timer sometimes skips a second. This is due to the fact that the
XBMC API sometimes doesn't respond fast enough to get the current player position.
This is purely a esthetic glitch, nothing more.
* Airplay supports starting a movie from any position, but the XBMC API does not expose a way
to do this. I've worked around this by just starting the movie from the beginning and then seeking
to the specified start position. This works, but you'll probably see a split second of the beginning
of the movie before XBMC seeks to the start position.
* It's not possible to stream DRM protocted content (yet).
* A lot of third party apps use m3u8 files for streaming content. Unfortunately XBMC, Plex and Boxee do not
support this format yet. See [this XBMC ticket](http://trac.xbmc.org/ticket/11175) for more information.
