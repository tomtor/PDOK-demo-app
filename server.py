# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import threading

import urllib.request
import time
import sys

import sqlite3

from logic import do_GET
from create import create_db

hostName = "localhost"
hostPort = 9000

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

create_db()

class MyServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    def do_GET(self):
        return do_GET(self)


myServer = ThreadedHTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
