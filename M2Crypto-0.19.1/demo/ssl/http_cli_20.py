import httplib, sys

def test_httplib():
    h = httplib.HTTPConnection('127.0.0.1', 80)
    h.set_debuglevel(1)
    h.putrequest('GET', '/')
    h.putheader('Accept', 'text/html')
    h.putheader('Accept', 'text/plain')
    h.putheader('Connection', 'close')
    h.endheaders()
    resp = h.getresponse()
    f = resp.fp
    while 1:
        data = f.readline()   
        if not data:
            break
        sys.stdout.write(data)
    f.close()
    h.close()

if __name__=='__main__':
    test_httplib()
