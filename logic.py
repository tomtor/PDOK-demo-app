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

def p(db):
    return '?' if db is None else '%s'
def p4(db):
    return '?,?,?,?' if db is None else '%s,%s,%s,%s'

def scrub(table_name):
    return ''.join( chr for chr in table_name if chr.isalnum() )

def scrubMail(mail_name):
    return ''.join( chr for chr in mail_name if (chr.isalnum() or chr == '.' or chr == '@' or chr == '_' or chr == '-') )

def do_GET(req, pc):
    if len(req.path) > 1000:
        req.send_error(400, "Too long (> 1000)", "utf-8")
        return

    qraw = req.path.split('/')

    if len(qraw) < 4:
        req.send_error(400, "Too few args", "utf-8")
        return

    req.send_response(200)
    if qraw[2] == 'activate':
        req.send_header("Content-type", "text/html")
    else:
        req.send_header("Content-type", "application/json")
    req.send_header("Access-Control-Allow-Origin", "*")
    req.end_headers()
    
    if pc is None:
        conn = sqlite3.connect('request.db')
    else:
        conn = pc
    c = conn.cursor()

    q = []
    for val in qraw:
        q.append(urllib.request.unquote(val))
    key = "d_" + scrub(q[2])

    if q[3] == 'add':
        try:
            c.execute("SELECT activated FROM datasets WHERE publicKey = " + p(pc)+";", (q[2],) )
            data = c.fetchone()
            if data[0] == 1:
                privUuid = str(uuid.uuid4())
                c.execute("INSERT INTO " + key + " (uuid, privUuid, ip, location) VALUES (" + p4(pc) + ");",
                    (str(uuid.uuid1()), privUuid, req.headers['X-Forwarded-For'], q[4]) )
                req.wfile.write(bytes('"'+privUuid+'"', "utf-8"))
            else:
                req.wfile.write(bytes("readonly", "utf-8"))
        except:
            print("add fail: " + req.path)
            req.wfile.write(bytes("false", "utf-8"))

    elif q[3] == 'get':
        try:
            if len(q) > 4 and len(q[4]) > 0:
                print(q[4])
                query = c.execute("SELECT uuid, location, ip, Timestamp FROM " + key
                    + " WHERE (Timestamp || uuid || COALESCE(ip,'') || location) LIKE "+p(pc)+";",
                    (q[4], ) )
            else:
                query = c.execute("SELECT uuid, location, ip, Timestamp FROM " + key + ";")
            first = True
            firstError = True
            req.wfile.write(bytes('[', "utf-8") )
            if not pc is None:
                query= c.fetchall()
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
                    row = '"'+str(r)+'"'
                if first:
                    req.wfile.write(bytes(row, "utf-8") )
                    first = False
                else:
                    req.wfile.write(bytes(', ' + row, "utf-8") )
            req.wfile.write(bytes(']', "utf-8") )
        except Exception as e:
            #print(str(e))
            print("get fail: " + req.path)
            req.wfile.write(bytes("false", "utf-8"))

    elif q[3] == 'delete':
        try:
            c.execute("DELETE FROM " + key + " WHERE privUuid = "+p(pc)+";", (q[4],) )
            req.wfile.write(bytes("true", "utf-8"))
        except:
            print("delete fail: " + req.path)
            req.wfile.write(bytes("false", "utf-8"))

    elif q[2] == 'dump':
        try:
            c.execute("SELECT publicKey FROM datasets WHERE privateKey = "+p(pc)+";", (q[3],) )
            data = c.fetchone()
            if data is None:
                print("dump fail: " + req.path)
                req.wfile.write(bytes("false", "utf-8"))
            else:
                req.wfile.write(bytes('[', "utf-8") )
                first = True
                if pc is None:
                    query= c.execute("SELECT * FROM d_" + scrub(data[0]) + ";")
                else:
                    c.execute("SELECT row_to_json(d_" + scrub(data[0]) + ") FROM d_" + scrub(data[0]) + ";")
                    query= c.fetchall()
                for r in query:
                    row = json.dumps(r) if pc is None else json.dumps(r[0])
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
        try:
            c.execute("SELECT publicKey FROM datasets WHERE privateKey = "+p(pc)+";", (q[3],) )
            data = c.fetchone()
            if data is None:
                req.wfile.write(bytes("false", "utf-8"))
            else:
                c.execute("SELECT count(*) FROM d_" + scrub(data[0]) + ";")
                cdata = c.fetchone()
                if cdata[0] == 0:
                    c.execute("DROP TABLE d_" + scrub(data[0]) + ";")
                    c.execute("DELETE FROM datasets WHERE privateKey = "+p(pc)+";", (q[3],) )
                    req.wfile.write(bytes("true", "utf-8"))
                else:
                    print("not empty: " + req.path)
                    req.wfile.write(bytes("false", "utf-8"))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            req.wfile.write(bytes("false", "utf-8"))

    elif q[2] == 'create':
        try:
            mail = q[3]
            if '@' not in mail:
                req.wfile.write(bytes("false", "utf-8"))
            else:
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
                c.execute("INSERT INTO datasets (privateKey, publicKey, activated, email) VALUES("+p(pc)+", "+p(pc)+", 0, "+p(pc)+");", (privateKey, publicKey, mail) )
                req.wfile.write(bytes("true", "utf-8"))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            req.wfile.write(bytes("false", "utf-8"))

    elif q[2] == 'activate':
        try:
            c.execute("SELECT publicKey FROM datasets WHERE privateKey = "+p(pc)+";", (q[3],) )
            data = c.fetchone()
            if data is None:
                req.wfile.write(bytes("false", "utf-8"))
            else:
                c.execute("UPDATE datasets SET activated = 1 WHERE privateKey = "+p(pc)+";", (q[3], ) )
                print("CREATE TABLE IF NOT EXISTS d_" + scrub(data[0]) + ";");
                if pc is None:
                    c.execute("CREATE TABLE IF NOT EXISTS d_" + scrub(data[0]) + " (uuid text, privUuid text, ip text, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, location text);");
                else:
                    c.execute("CREATE TABLE IF NOT EXISTS d_" + scrub(data[0]) + " (uuid text, privUuid text, ip text, Timestamp timestamp DEFAULT CURRENT_TIMESTAMP, location text);");
                req.wfile.write(bytes('<html><body>Welcome...<br/><br/><a href="https://github.com/tomtor/PDOK-demo-app">Documentation</a></body></html>', "utf-8"))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            req.wfile.write(bytes("false", "utf-8"))

    elif q[2] == 'readonly':
        try:
            c.execute("UPDATE datasets SET activated = "+p(pc)+" WHERE privateKey = "+p(pc)+";", (1-int(q[4]), q[3]) )
            req.wfile.write(bytes("true", "utf-8"))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            req.wfile.write(bytes("false", "utf-8"))

    else:
        print("unknown operation: " + req.path)
        req.wfile.write(bytes("false", "utf-8"))

    # Log all requests
    c.execute("INSERT INTO requests (path) VALUES ("+p(pc)+");", (req.path,) )
    conn.commit()
    if pc is None:
        conn.close()
