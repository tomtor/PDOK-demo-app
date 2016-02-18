import urllib.request
import urllib.parse
import json

hostName = "localhost"
hostPort = "9000"
key	 = "d89d5ee2-d347-11e5-9d78-bcaec5c2cce2";

server = "http://" + hostName + ":" + hostPort + "/test/"
serverKey = server + key + "/"

print("readonly: 0")
print(urllib.request.urlopen(server + "readonly/" + key + "/0").read())
print("add:")
print(urllib.request.urlopen(serverKey + "add/"
	+ urllib.parse.quote('''
		{"type": "Feature", "geometry": {"type": "Point",
		"coordinates": [6.1884810525762735, 52.678157083226424]},
		"properties": {"kind": "Animal", "name": "Snake"}}''',
		safe = '\0')).read())
print("readonly: 1")
print(urllib.request.urlopen(server + "readonly/" + key + "/1").read())
print("add no JSON 2:")
print(urllib.request.urlopen(serverKey + "add/" + urllib.parse.quote("Some random &*#@^&@%#(*h% data...", '')).read())
print("add:")
print(urllib.request.urlopen(serverKey + "add/"
	+ urllib.parse.quote('''
		{"type": "Feature", "geometry": {"type": "Point",
		"coordinates": [6.1884810525762735, 52.678157083226424]},
		"properties": {"kind": "Animal", "name": "Snake"}}''',
		safe = '\0')).read())
print("readonly: 0")
print(urllib.request.urlopen(server + "readonly/" + key + "/0").read())
print("add no JSON:")
print(urllib.request.urlopen(serverKey + "add/" + "JustSomeText...").read());
print("add no JSON 2:")
print(urllib.request.urlopen(serverKey + "add/" + urllib.parse.quote("Some random &*#@^&@%#(*h% data...", '')).read())

print("get:")
print(urllib.request.urlopen(serverKey + "get/" ).read())
#print("get: %nak%")
#print(urllib.request.urlopen(serverKey + "get/" + urllib.parse.quote("%nak%", '')).read())

#print("delete:")
#print(urllib.request.urlopen(serverKey + "delete/" + "3b5c87b3-9e26-41bd-8bda-4858d23e35f2").read())
#print("delete2:")
#print(urllib.request.urlopen(serverKey + "delete/" + "ddcf5c18-6725-49f2-bce5-897aa41a4262").read())

#print("dump:")
#print(urllib.request.urlopen(server + "dump/" + key).read())

#print("drop:")
#print(urllib.request.urlopen(server + "drop/" + key).read())

#print("dump:")
#print(urllib.request.urlopen(server + "dump/" + key).read())

#print("create:")
#print(urllib.request.urlopen(server + "create/postmaster@v7f.eu").read())
#
#print("activate:")
#print(urllib.request.urlopen(server + "activate/1c6e093d-6df6-4e63-b19b-b3be8fb8d606").read())
#print("activate2:")
#print(urllib.request.urlopen(server + "activate/85c6e606-9701-44ea-b9d5-8c9c2f7ed428").read())
#
#print("add2:")
#print(urllib.request.urlopen(server + "c6f3800f-d423-11e5-9d78-bcaec5c2cce2" + "/add/"
#	+ urllib.parse.quote('''
#		{"type": "Feature", "geometry": {"type": "Point",
#		"coordinates": [6.1884810525762735, 52.678157083226424]},
#		"properties": {"kind": "Animal", "name": "Snake"}}''',
#		safe = '\0')).read())
#print("get2:")
#print(urllib.request.urlopen(server + "c6f3800f-d423-11e5-9d78-bcaec5c2cce2" + "/get/").read())
