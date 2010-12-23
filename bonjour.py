import select
import pybonjour

def register_service(name, regtype, port):
    def register_callback(sdRef, flags, errorCode, name, regtype, domain):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            print 'Registered service:'
            print '  name    =', name
            print '  regtype =', regtype
            print '  domain  =', domain


    service = pybonjour.DNSServiceRegister(name = name,
                                         regtype = regtype,
                                         port = port,
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