# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import time
import uuid
import json
import sys

import sqlite3

import smtplib
from email.mime.text import MIMEText

hostName = "localhost"
hostPort = 9000

conn = sqlite3.connect('request.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS requests
             (path text);''')
c.execute('''CREATE TABLE IF NOT EXISTS datasets
             (privateKey text, publicKey text, activated integer);''')
c.execute('''CREATE TABLE IF NOT EXISTS d_d89d5ee2d34711e59d78bcaec5c2cce2
             (uuid text, privUuid text, ip text, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, location text);''')
c.execute('''INSERT INTO datasets (privateKey, publicKey, activated) VALUES("d89d5ee2-d347-11e5-9d78-bcaec5c2cce2", "d89d5ee2-d347-11e5-9d78-bcaec5c2cce2", 1);''')
conn.commit()

def scrub(table_name):
    return ''.join( chr for chr in table_name if chr.isalnum() )

class MyServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        if len(self.path) > 1000 :
            self.wfile.write(bytes("Too long (> 1000)", "utf-8"))
            return

        #if self.path[:16] != '/pdok-demo-data/' :
        #    self.wfile.write(bytes("Expect /pdok-demo-data/", "utf-8"))
        #    return

        qraw = self.path.split('/')
        q = []
        for val in qraw :
            q.append(urllib.request.unquote(val))
        key = "d_" + scrub(q[2])

        if q[3] == 'add' :
            try :
                privUuid = str(uuid.uuid4())
                c.execute("INSERT INTO " + key + " (uuid, privUuid, ip, location) VALUES (?,?,?,?);",
                    (str(uuid.uuid1()), privUuid, self.headers['X-Forwarded-For'], q[4]) )
                self.wfile.write(bytes(privUuid, "utf-8"))
            except:
                print("add fail: " + self.path)
                self.wfile.write(bytes("false", "utf-8"))

        elif q[3] == 'get' :
            self.wfile.write(bytes('[', "utf-8") )
            first = True
            where = "1"
            if len(q) > 4 and len(q[4]) > 0 :
                print(q[4])
                query = c.execute("SELECT uuid, location, ip, Timestamp FROM " + key + " WHERE location LIKE ?",
                    (q[4], ) )
            else :
                query = c.execute("SELECT uuid, location, ip, Timestamp FROM " + key + ";")
            for r in query :
                try :
                    js= json.loads(r[1])
                    js["properties"]["uuid"]= r[0]
                    js["properties"]["ip_info"]= r[2]
                    js["properties"]["timestamp"]= r[3]
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

        elif q[3] == 'delete' :
            try :
                c.execute("DELETE FROM " + key + " WHERE privUuid = ?;", (q[4],) )
                self.wfile.write(bytes("true", "utf-8"))
            except:
                print("Unexpected error:", sys.exc_info()[0])
                self.wfile.write(bytes("false", "utf-8"))

        elif q[2] == 'dump' :
            c.execute("SELECT publicKey FROM datasets WHERE privateKey = ?", (q[3],) )
            data = c.fetchone()
            if data is None :
                self.wfile.write(bytes("false", "utf-8"))
            else :
                try :
                    self.wfile.write(bytes('[', "utf-8") )
                    first = True
                    for r in c.execute("SELECT * FROM d_" + scrub(data[0]) + ";") :
                        row = json.dumps(r)
                        if first :
                            self.wfile.write(bytes(row, "utf-8") )
                            first = False
                        else :
                            self.wfile.write(bytes(', ' + row, "utf-8") )
                    self.wfile.write(bytes(']', "utf-8") )
                except :
                    print("Unexpected error:", sys.exc_info()[0])
                    self.wfile.write(bytes("false", "utf-8"))

        elif q[2] == 'drop' :
            c.execute("SELECT publicKey FROM datasets WHERE privateKey = ?", (q[3],) )
            data = c.fetchone()
            if data is None :
                self.wfile.write(bytes("false", "utf-8"))
            else :
                try :
                    c.execute("SELECT count(*) FROM d_" + scrub(data[0]) + ";")
                    cdata = c.fetchone()
                    if cdata[0] == 0 :
                        c.execute("DROP TABLE d_" + scrub(data[0]) + ";")
                        c.execute("DELETE FROM datasets WHERE privateKey = ?", (q[3],) )
                        self.wfile.write(bytes("true", "utf-8"))
                    else :
                        print("not empty")
                        self.wfile.write(bytes("false", "utf-8"))
                except :
                    print("Unexpected error:", sys.exc_info()[0])
                    self.wfile.write(bytes("false", "utf-8"))

        elif q[2] == 'create' :
            mail = q[3]
            if '@' not in mail :
                self.wfile.write(bytes("false", "utf-8"))
                return
            publicKey = str(uuid.uuid1())
            privateKey = str(uuid.uuid4())
            js= {'private': privateKey, 'public': publicKey }
            #self.wfile.write(bytes(json.dumps(js), "utf-8"))
            print(js)
            # Mail for activation instead of returning it:
            msg = MIMEText("Private key: " + privateKey
                + "\nPublic key: " + publicKey
                + "\n\nActivate: http://v7f.eu/pdok-demo-data/activate/" + privateKey)
            msg['Subject'] = 'Your data keys and activation link'
            msg['From'] = 'postmaster@v7f.eu'
            msg['To'] = mail 
            s = smtplib.SMTP('localhost')
            s.send_message(msg)
            s.quit()
            c.execute("INSERT INTO datasets (privateKey, publicKey, activated) VALUES(?, ?, 0);", (privateKey, publicKey) )
            self.wfile.write(bytes("true", "utf-8"))

        elif q[2] == 'activate' :
            c.execute("SELECT publicKey FROM datasets WHERE privateKey = ?", (q[3],) )
            data = c.fetchone()
            if data is None :
                self.wfile.write(bytes("false", "utf-8"))
            else :
                c.execute("UPDATE datasets SET activated = 1 WHERE privateKey = ?;", (q[3], ) )
                print("CREATE TABLE IF NOT EXISTS d_" + scrub(data[0]) + ";");
                c.execute("CREATE TABLE IF NOT EXISTS d_" + scrub(data[0]) + " (uuid text, privUuid text, ip text, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, location text);");
                self.wfile.write(bytes("true", "utf-8"))

        else :
            self.wfile.write(bytes("false", "utf-8"))

        # Log all requests
        c.execute("INSERT INTO requests (path) VALUES (?);", (self.path,) )
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
