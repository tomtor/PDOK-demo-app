# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import threading

import urllib.request
import time
import sys

import sqlite3
import psycopg2

from logic import do_GET
from create import create_db

hostName = "localhost"
hostPort = 9000

#pgConn = None
pgConn = psycopg2.connect("dbname='simplestore' user='simple' host='swan.v7f.eu' password='simple'")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

create_db(pgConn)

class MyServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    def do_GET(self):
        return do_GET(self, pgConn)


myServer = ThreadedHTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
