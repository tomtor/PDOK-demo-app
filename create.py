# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys

import sqlite3

def create_db():
    conn = sqlite3.connect('request.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS requests
             (path text, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);''')
    c.execute('''CREATE TABLE IF NOT EXISTS datasets
             (privateKey text, publicKey text, activated integer,
             email text, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);''')
    c.execute('''CREATE TABLE IF NOT EXISTS d_d89d5ee2d34711e59d78bcaec5c2cce2
             (uuid text, privUuid text, ip text,
             Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, location text);''')
    c.execute('''INSERT INTO datasets (privateKey, publicKey, activated)
             VALUES("d89d5ee2-d347-11e5-9d78-bcaec5c2cce2", "d89d5ee2-d347-11e5-9d78-bcaec5c2cce2", 1);''')
    conn.commit()

