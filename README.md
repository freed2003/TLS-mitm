# TLS-mitm
A small script that acts as a proxy and logs traffic

You may use OpenSSL to generate the required files through 
```openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out cert.pem```

Run the proxy with
```python proxy.py```
