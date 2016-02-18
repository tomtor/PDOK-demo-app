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


def scrub(table_name):
    return ''.join( chr for chr in table_name if chr.isalnum() )

def scrubMail(mail_name):
    return ''.join( chr for chr in mail_name if (chr.isalnum() or chr == '.' or chr == '@' or chr == '_' or chr == '-') )

def do_GET(req):
    conn = sqlite3.connect('request.db')
    c = conn.cursor()

    qraw = req.path.split('/')
    req.send_response(200)
    if qraw[2] == 'activate':
        req.send_header("Content-type", "text/html")
    else:
        req.send_header("Content-type", "application/json")
    req.send_header("Access-Control-Allow-Origin", "*")
    req.end_headers()
    
    if len(req.path) > 1000:
        req.wfile.write(bytes("Too long (> 1000)", "utf-8"))
        return

    q = []
    for val in qraw:
        q.append(urllib.request.unquote(val))
    key = "d_" + scrub(q[2])

    if q[3] == 'add':
        try:
            c.execute("SELECT activated FROM datasets WHERE publicKey = ?", (q[2],) )
            data = c.fetchone()
            if data[0] == 1:
                privUuid = str(uuid.uuid4())
                c.execute("INSERT INTO " + key + " (uuid, privUuid, ip, location) VALUES (?,?,?,?);",
                    (str(uuid.uuid1()), privUuid, req.headers['X-Forwarded-For'], q[4]) )
                req.wfile.write(bytes(privUuid, "utf-8"))
            else:
                req.wfile.write(bytes("readonly", "utf-8"))
        except:
            print("add fail: " + req.path)
            req.wfile.write(bytes("false", "utf-8"))

    elif q[3] == 'get':
        req.wfile.write(bytes('[', "utf-8") )
        if len(q) > 4 and len(q[4]) > 0:
            print(q[4])
            query = c.execute("SELECT uuid, location, ip, Timestamp FROM " + key
                + " WHERE (Timestamp || uuid || COALESCE(ip,'') || location) LIKE ?",
                (q[4], ) )
        else:
            query = c.execute("SELECT uuid, location, ip, Timestamp FROM " + key + ";")
        first = True
        firstError = True
        for r in query:
            try:
                js= json.loads(r[1])
                js["properties"]["uuid"]= r[0]
                js["properties"]["ip_info"]= r[2]
                js["properties"]["timestamp"]= r[3]
                row = json.dumps(js)
            except:
                if firstError:
                    print("Cannot parse JSON")
                    firstError = False
                row = str(r)
            if first:
                req.wfile.write(bytes(row, "utf-8") )
                first = False
            else:
                req.wfile.write(bytes(', ' + row, "utf-8") )
        req.wfile.write(bytes(']', "utf-8") )

    elif q[3] == 'delete':
        try:
            c.execute("DELETE FROM " + key + " WHERE privUuid = ?;", (q[4],) )
            req.wfile.write(bytes("true", "utf-8"))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            req.wfile.write(bytes("false", "utf-8"))

    elif q[2] == 'dump':
        c.execute("SELECT publicKey FROM datasets WHERE privateKey = ?", (q[3],) )
        data = c.fetchone()
        if data is None:
            req.wfile.write(bytes("false", "utf-8"))
        else:
            try:
                req.wfile.write(bytes('[', "utf-8") )
                first = True
                for r in c.execute("SELECT * FROM d_" + scrub(data[0]) + ";"):
                    row = json.dumps(r)
                    if first:
                        req.wfile.write(bytes(row, "utf-8") )
                        first = False
                    else:
                        req.wfile.write(bytes(', ' + row, "utf-8") )
                req.wfile.write(bytes(']', "utf-8") )
            except:
                print("Unexpected error:", sys.exc_info()[0])
                req.wfile.write(bytes("false", "utf-8"))

    elif q[2] == 'drop':
        c.execute("SELECT publicKey FROM datasets WHERE privateKey = ?", (q[3],) )
        data = c.fetchone()
        if data is None:
            req.wfile.write(bytes("false", "utf-8"))
        else:
            try:
                c.execute("SELECT count(*) FROM d_" + scrub(data[0]) + ";")
                cdata = c.fetchone()
                if cdata[0] == 0:
                    c.execute("DROP TABLE d_" + scrub(data[0]) + ";")
                    c.execute("DELETE FROM datasets WHERE privateKey = ?", (q[3],) )
                    req.wfile.write(bytes("true", "utf-8"))
                else:
                    print("not empty")
                    req.wfile.write(bytes("false", "utf-8"))
            except:
                print("Unexpected error:", sys.exc_info()[0])
                req.wfile.write(bytes("false", "utf-8"))

    elif q[2] == 'create':
        mail = q[3]
        if '@' not in mail:
            req.wfile.write(bytes("false", "utf-8"))
            return
        publicKey = str(uuid.uuid1())
        privateKey = str(uuid.uuid4())
        js= {'private': privateKey, 'public': publicKey }
        #req.wfile.write(bytes(json.dumps(js), "utf-8"))
        print(js)
        # Mail for activation instead of directly returning it:
        msg = MIMEText("Private key: " + privateKey
            + "\nPublic key: " + publicKey
            + "\n\nActivate: http://v7f.eu/pdok-demo-data/activate/" + privateKey)
        msg['Subject'] = 'Your data keys and activation link'
        msg['From'] = 'postmaster@v7f.eu'
        msg['To'] = scrubMail(mail)
        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()
        c.execute("INSERT INTO datasets (privateKey, publicKey, activated, email) VALUES(?, ?, 0, ?);", (privateKey, publicKey, mail) )
        req.wfile.write(bytes("true", "utf-8"))

    elif q[2] == 'activate':
        c.execute("SELECT publicKey FROM datasets WHERE privateKey = ?", (q[3],) )
        data = c.fetchone()
        if data is None:
            req.wfile.write(bytes("false", "utf-8"))
        else:
            c.execute("UPDATE datasets SET activated = 1 WHERE privateKey = ?;", (q[3], ) )
            print("CREATE TABLE IF NOT EXISTS d_" + scrub(data[0]) + ";");
            c.execute("CREATE TABLE IF NOT EXISTS d_" + scrub(data[0]) + " (uuid text, privUuid text, ip text, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, location text);");
            req.wfile.write(bytes('<html><body>Welcome...<br/><br/><a href="https://github.com/tomtor/PDOK-demo-app">Documentation</a></body></html>', "utf-8"))

    elif q[2] == 'readonly':
            c.execute("UPDATE datasets SET activated = ? WHERE privateKey = ?;", (1-int(q[4]), q[3]) )
            req.wfile.write(bytes("true", "utf-8"))

    else:
        req.wfile.write(bytes("false", "utf-8"))

    # Log all requests
    c.execute("INSERT INTO requests (path) VALUES (?);", (req.path,) )
    conn.commit()
    conn.close()
