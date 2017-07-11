# Howto

# Generate Certs and place it in the dirs showed in Treeview

## Generate Certs for nginx
Create the CA Key and Certificate for signing Client Certs
```
openssl genrsa -des3 -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.crt
```

Create the Server Key, CSR, and Certificate
```
openssl genrsa -des3 -out server.key 1024
openssl req -new -key server.key -out server.csr
```

We're self signing our own server cert here.  This is a no-no in production.
```
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt
```

Create the Client Key and CSR
```
openssl genrsa -des3 -out client.key 1024
openssl req -new -key client.key -out client.csr
```

Sign the client certificate with our CA cert.  Unlike signing our own server cert, this is what we want to do.
```
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out client.crt
```

## Generate Xpra Certs
```
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365
```


# TreeView
```
├── app
│   ├── uwsgi.ini
│   ├── uwsgi.py
│   └── xpraauth.py
├── certs_nginx
│   ├── private
│   │   ├── ca.key
│   │   ├── client.csr
│   │   ├── client.key
│   │   └── server.key
│   └── public
│       ├── ca.crt
│       └── server.crt
├── certs_xpra
│   ├── private
│   │   └── server.key
│   └── public
│       └── server.crt
├── Dockerfile
├── nginx.conf
├── README.md
├── requirements.txt
├── supervisord.conf
├── uwsgi.ini
└── xprafile
    ├── xpra_auth_file
    └── xpraauth.log
```

# RestAPI Docu
## GET /api/1/targethosts
```
HTTP/1.0 200 OK
-get a List of all possible xpra_auth_file entries based on its UIDs as array
format of sending data:
-
format of answer:
[ {"id": "UUID" }, ... ]
example:
curl -H "Content-Type: application/json" http://localhost:5000/api/1/targethosts -X GET -v
response:
[{"id": "0b555840-c3e8-46ca-ad81-66efb41eab52"}, {"id": "263deb0a-13ba-4bb1-844b-e04d55324feb"}]
```

## POST /api/1/targethosts
```
HTTP/1.0 201 CREATED
-post a new xpra proxy entry in format USERNAME|PASSWORD|UID|GID|SESSION_URI|ENV_VARS|SESSION_OPTIONS, described on https://xpra.org/trac/wiki/ProxyServer
format of sending data:
{"username": "string", "targethost": "string", "password": "string"}
format of answer:
{"id": "UUID" }
example:
curl -H "Content-Type: application/json" http://localhost:5000/api/1/targethosts -d '{"username": "tr8384", "targethost": "xpra2.svc.firecloud", "password": "geheimespw"}' -X POST -v -k
response:
{"id": "720c056f-138d-411f-88f7-5470af9ae42b"}
```

## GET /api/1/targethosts/`<UID>`
```
HTTP/1.0 200 OK
-get list for a special entry with a given UID
format of sending data:
{"id": "UUID" }
format of answer:
{"username": "string", "targethost": "string", "password": "string", "targethostUUID": "UUID"}
example:
curl -H "Content-Type: application/json" http://localhost:5000/api/1/targethosts/720c056f-138d-411f-88f7-5470af9ae42b -X GET -v
response:
{"username": "tr8384", "targethost": "xpra2.svc.firecloud", "password": "geheimespw", "targethostUUID": "720c056f-138d-411f-88f7-5470af9ae42b"}
```

## POST /api/1/targethosts/`<UID>`
```
HTTP/1.0 200 OK
-updates an entry for a given UID
format of sending data:
{"username": "string", "targethost": "string", "password": "string"}
format of answer:
{"id": "UUID" }
example:
curl -H "Content-Type: application/json" http://localhost:5000/api/1/targethosts/720c056f-138d-411f-88f7-5470af9ae42b -d '{"username": "tr8384", "targethost": "xpra2.svc.firecloud", "password": "geheimespw222"}' -X POST -v -k
response:
{"id": "720c056f-138d-411f-88f7-5470af9ae42b"}
```

## DELETE /api/1/targethosts/`<UID>`
```
HTTP/1.0 204 OK
-deletes an entry for a given UID
format of sending data:
[ {"id": "UUID" }]
format of answer:
-
example:
curl -H "Content-Type: application/json" http://localhost:5000/api/1/targethosts/720c056f-138d-411f-88f7-5470af9ae42b -X DELETE -v
reponse:
-
```

## PUT /api/1/targethosts/`<UID>`
```
same as POST /api/1/targethosts/<UID>
```


