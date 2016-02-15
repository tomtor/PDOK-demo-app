# PDOK-demo-app
A collection of PDOK (http://www.pdok.nl) example applications

* index.html (http://v7f.eu/public/PDOK)
  * Shows a simple Leaflet map.
  * Clicking shows the coordinates.

* add-data.html (http://v7f.eu/public/PDOK/add-data.html)
  * Adds permanent data to a map.

* server.py: Implements the server side storage for add-data.html
  * Written in Python3
  * Stores the added data in an SQLite database.
  * Private/public access keys with mail activation

* test-server.py
  * Test script which demonstrates the API
