import os
import platform
try:
    import resource
except ImportError:
    """
    Not available on Windows
    """
    pass    

def clear_folder(folder):
    """
    Remove the given folder's content.
    """
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            print e
            
def clean_hostname(hostname):
    """
    Remove the .local appendix of a hostname.
    """
    if hostname:
        return hostname.replace('.local', '')
        
def duration_to_seconds(duration_str):
    """
    Acceptable formats are: "MM:SS", "HH:MM" and "HH:MM:SS".
    """
    values = duration_str.split(':')
    
    if len(values) == 1:
        raise Exception('Invalid value supplied: %s', duration_str)
    
    seconds = 0
    
    for i, val in enumerate(reversed(values)):        
        val = int(val) * pow(60, i)
        seconds = seconds + val
        
    return seconds        
        
"""
The following code is originating from Gunicorn:
https://github.com/benoitc/gunicorn
"""        
        
MAXFD = 1024
if (hasattr(os, "devnull")):
   REDIRECT_TO = os.devnull
else:
   REDIRECT_TO = "/dev/null"        
        
def get_maxfd():
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = MAXFD
    return maxfd
            
def daemonize():
    """
    Currently only implemented for Unix like systems.
    """
    if platform.system() == 'Windows':
        raise Exception('Daemonizing is currently not supported on Windows.')
       
    if os.fork() == 0: 
        os.setsid()
        if os.fork():
            os._exit(0)
    else:
        os._exit(0)
                
    os.umask(0)
    maxfd = get_maxfd()

    # Iterate through and close all file descriptors.
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:	# ERROR, fd wasn't open to begin with (ignored)
            pass

    os.open(REDIRECT_TO, os.O_RDWR)
    os.dup2(0, 1)
    os.dup2(0, 2)    