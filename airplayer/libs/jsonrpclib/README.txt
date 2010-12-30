XBMC is currently not fully compliant to the JSON-RPC 2.0 spec.
When a single argument is passed an array with one element
should be provied according to the spec, however XBMC expects a
single value in this case.

See http://forum.xbmc.org/showpost.php?p=671587&postcount=591

I've patched jsonrpc.py to reflect this required behaviour for
interacting with XBMC.