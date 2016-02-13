from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import time

import sqlite3

hostName = "localhost"
hostPort = 9000

conn = sqlite3.connect('request.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS requests
             (path text)''')
c.execute('''CREATE TABLE IF NOT EXISTS markers
             (location text)''')

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

        r = urllib.request.unquote(self.path)
        r = r[15:] # strip /pdok-demo-data/
        print(self.path)

        if r[:5] == '/add/' :
            c.execute("INSERT INTO markers (location) VALUES (?)", (r[5:],) )

        elif r[:5] == '/get/' :
            self.wfile.write(bytes('[', "utf-8") )
            first = True
            for row in c.execute("SELECT location FROM markers") :
                if first :
                    self.wfile.write(bytes(row[0], "utf-8") )
                    first = False
                else :
                    self.wfile.write(bytes(', ' + row[0], "utf-8") )
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
