import logging
import settings

logger = logging.getLogger('airplayer')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

if getattr(settings, 'DEBUG', None) and settings.DEBUG:
    log_level = logging.DEBUG
else:
    log_level = logging.WARNING    
    
logger.setLevel(log_level)    