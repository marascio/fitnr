#!/usr/bin/env python
#
# $Id: serveit.py 236 2008-07-10 02:36:21Z louis $

import os, os.path
import SimpleHTTPServer as http
import SocketServer

class MyHTTPRequestHandler(http.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.path = '/build' + self.path
        return http.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == '__main__':
    httpd = None
    port  = 8000

    try:
        handler = MyHTTPRequestHandler
        httpd = SocketServer.TCPServer(("", port), handler)
        print 'starting server on port', port
        httpd.serve_forever()
    except KeyboardInterrupt:
        if httpd is not None:
            print '', 'shutting down'
            httpd.socket.close()
    except Exception, e:
        print 'Exception caught:', e

