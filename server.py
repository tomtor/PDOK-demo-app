from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import time
import uuid
import json
import sys

import sqlite3

hostName = "localhost"
hostPort = 9000

conn = sqlite3.connect('request.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS requests
             (path text)''')
c.execute('''CREATE TABLE IF NOT EXISTS markers
             (uuid text, location text)''')

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        if len(self.path) > 1000 :
            self.wfile.write(bytes("Too long (> 1000)", "utf-8"))
            return

        if self.path[:16] != '/pdok-demo-data/' :
            self.wfile.write(bytes("Expect /pdok-demo-data/", "utf-8"))
            return

        qraw = self.path.split('/')
        q = []
        for val in qraw :
            q.append(urllib.request.unquote(val))
        key = q[2]

        if q[3] == 'add' :
            c.execute("INSERT INTO markers (uuid, location) VALUES (?,?)", (str(uuid.uuid1()), q[4]) )

        elif q[3] == 'get' :
            self.wfile.write(bytes('[', "utf-8") )
            first = True
            for r in c.execute("SELECT uuid, location FROM markers") :
                try :
                    js= json.loads(r[1])
                    js["properties"]["uuid"]= r[0]
                    row = json.dumps(js)
                except :
                    print("Unexpected error:", sys.exc_info()[0])
                    row = r[1]
                if first :
                    self.wfile.write(bytes(row, "utf-8") )
                    first = False
                else :
                    self.wfile.write(bytes(', ' + row, "utf-8") )
            self.wfile.write(bytes(']', "utf-8") )
            return

        self.wfile.write(bytes("true", "utf-8"))
        
        # Log all requests
        c.execute("INSERT INTO requests (path) VALUES (?)", (self.path,) )
        conn.commit()


myServer = HTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))

conn.close()
