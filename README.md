# PDOK-demo-app
A collection of PDOK (http://www.pdok.nl) example applications

See http://school-crowd.v7f.eu which is built on this framework.

* simple.html (http://v7f.eu/public/PDOK/simple.html)
  * Shows a simple Leaflet map.
  * Clicking shows the coordinates.

* add-data.html (https://v7f.eu/public/PDOK/add-data.html)
  * Adds permanent data to a map.

* server.py: Implements the server side storage for add-data.html
  * Written in Python3
  * Stores the added data in an SQLite or PostgreSQL database.
  * Private/public access keys with mail activation
  * With Swagger API documentation: http://v7f.eu/public/PDOK/dist

* test-server.py
  * Test script which demonstrates the API

# Server API documentation

The server.py implementation is intended as a Self Service (JSON) data storage for small datasets.

# See the Swagger API specification at: http://v7f.eu/public/PDOK/dist

## Private API calls

### ../create/my.email@domain.demo

Creates a new database and private and public access keys (UUIDs).
A mail is sent to the specified mail address with an activation link.

### ../activate/UUID

Activate the database with the specified PRIVATE UUID.

### ../drop/UUID

Drop the database with the specified PRIVATE UUID.

Note that it must be empty before it can be dropped!

### ../dump/UUID

Dumps all the data in the database with the private UUID key including the private UUID object keys.

### ../readonly/UUID/{0|1}

Makes the database with the private UUID key readonly (1) or read/write (0).


## Public API calls

### ../UUID/add/data

Adds data to the database with the specified PUBLIC UUID.

Data is prefered in (Geo)JSON format, but that is not mandatory.

In addition to the original data, a TimeStamp, the IP-Address, a public UUID and a private UUID are added.  The private object UUID key is returned. This key is needed for the "delete" call.

### ../UUID/delete/UUID2

Delete object with private key UUID2 from database UUID

### ../UUID/get/LIKE-string

Retrieve the data which matches the optional SQL LIKE string.
The TimeStamp, IP-Address and public UUID are added as properties.

