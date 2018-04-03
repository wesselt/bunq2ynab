from datetime import datetime
import json
import sys
import requests
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization


url = "https://api.bunq.com/"


def read_file(fname):
    with open(fname, 'r') as f:
        return f.read()


def read_token(fname):
    return read_file(fname).rstrip("\n")


def read_public_key(fname):
    with open(fname, 'br') as f:
        data = f.read()
    key = serialization.load_pem_public_key(data, default_backend())
    if not isinstance(key, rsa.RSAPublicKey):
        raise Exception("Public key is not an RSA key")
    return base64.b64encode(key).decode("utf-8")

request_id = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
server_token = read_token('server_token.txt')
api_token = read_token('api_token.txt')
public_key = read_file('public_key.txt')
    
method = "v1/installation"
data = {
    "client_public_key": public_key
}

headers = {
    'Cache-Control': 'no-cache',
    'User-Agent': 'bunq2ynab',
    'X-Bunq-Client-Request-Id': request_id,
    'X-Bunq-Geolocation': '0 0 0 0 NL',
    'X-Bunq-Language': 'en_US',
    'X-Bunq-Region': 'nl_NL'
}

print(data)
print("-----")
r = requests.post(url + method, headers=headers, data=json.dumps(data))
print("-----")
print(r.request.body)
print("-----")
print(r.json())
