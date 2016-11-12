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

hostName = "0.0.0.0"
hostPort = 9000

conConfig = "dbname='simplestore' user='simple' host='localhost' password='simple'"

pgConn = psycopg2.connect(conConfig)

create_db(pgConn)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class MyServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    def do_GET(self):
        global pgConn
        try:
            pgConn.isolation_level
        except psycopg2.OperationalError:
            pgConn = psycopg2.connect(conConfig)
        return do_GET(self, pgConn)


myServer = ThreadedHTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
