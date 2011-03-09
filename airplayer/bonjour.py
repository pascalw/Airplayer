import select
import pybonjour
import logging
import appletv

logger = logging.getLogger('airplayer')

def register_service(name, regtype, port):
    def register_callback(sdRef, flags, errorCode, name, regtype, domain):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            logger.debug('Registered bonjour service %s.%s', name, regtype)

    record = pybonjour.TXTRecord(appletv.DEVICE_INFO)
    
    service = pybonjour.DNSServiceRegister(name = name,
                                         regtype = regtype,
                                         port = port,
                                         txtRecord = record,
                                         callBack = register_callback)

    try:
        try:
            while True:
                ready = select.select([service], [], [])
                if service in ready[0]:
                    pybonjour.DNSServiceProcessResult(service)
        except KeyboardInterrupt:
            pass
    finally:
        service.close()