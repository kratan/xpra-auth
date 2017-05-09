# Howto

# Generate Certs and place it in the dirs showed in Treeview

##Generate Certs for nginx
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

# Generate Xpra Certs
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
