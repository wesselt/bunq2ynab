import base64
from OpenSSL import crypto
import json
import os
import requests
import sys


url = "https://api.bunq.com/"
private_key_file = "private_key.txt"
public_key_file = "public_key.txt"


def read_file(fname):
    try:
        with open(fname, 'r') as f:
            return f.read()
    except:
        pass


def write_file(fname, data):
    with open(fname, 'w') as f:
        f.write(data)


def delete_file(fname):
    os.unlink(fname)


# -----------------------------------------------------------------------------

def get_api_token():
    token = read_file("api_token.txt")
    if token:
        return token.rstrip("\n")
    raise Exception("File api_token.txt not found.  Add an API key " +
                    "using the app and store it in api_token.txt.")


def get_installation_token():
    token = read_token("installation_token.txt")
    if token:
        return token.rstrip("\n")
    raise Exception("Not implemented yet")


def get_session_token():
    token = read_token("session_token.txt")
    if token:
        return token.rstrip("\n")
    raise Exception("Not implemented yet")


def get_private_key():
    pem = read_file(private_key_file)
    if pem:
        return crypto.load_privatekey(crypto.FILETYPE_PEM, pem, password)
    print ("Generating new private key...")
    key = crypto.PKey()
    pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    delete_file(public_key_file)
    write_file(private_key_file, pem)
    return key


def get_public_key():
    pem = read_file(public_key_file)
    if pem:
        return crypto.load_publickey(crypto.FILETYPE_PEM, pem)
    raise Exception("Not implemented yet")


# -----------------------------------------------------------------------------

def sign(action, method, headers, data = ''):
    if "device-server" in method or "session-server" in method:
        headers['X-Bunq-Client-Authentication'] = get_installation_token()
    else:
        headers['X-Bunq-Client-Authentication'] = get_session_token()
    ciphertext = action + " /" + method + "\n"
    for name in sorted(headers.keys()):
        ciphertext += name + ": " + headers[name] + "\n"
    ciphertext += "\n" + data
    private_key = get_private_key()
    sig = crypto.sign(private_key, ciphertext, 'sha256')
    sig_str = base64.b64encode(sig).decode("utf-8")
    headers['X-Bunq-Client-Signature'] = sig_str


def default_headers():
    return {
        'Cache-Control': 'no-cache',
        'User-Agent': 'bunq2ynab',
        'X-Bunq-Client-Request-Id': '0',
        'X-Bunq-Geolocation': '0 0 0 0 NL',
        'X-Bunq-Language': 'en_US',
        'X-Bunq-Region': 'nl_NL'
    }


# -----------------------------------------------------------------------------

def get(method):
    headers = default_headers()
    sign('GET', method, headers)
    reply = requests.get(url + method, headers=headers)
    result = reply.json()
    if "Error" in result:
        raise Exception(result["Error"][0]["error_description"])
    return result["Response"]


def get_content(method):
    headers = default_headers()
    sign('GET', method, headers)
    reply = requests.get(url + method, headers=headers)
    return reply.text


def post(method, data_obj):
    data = json.dumps(data_obj)
    headers = default_headers()
    sign('POST', method, headers, data)
    reply = requests.post(url + method, headers=headers, data=data)
    result = reply.json()
    if "Error" in result:
        raise Exception(result["Error"][0]["error_description"])
    return result["Response"]


def delete(method):
    headers = default_headers()
    sign('DELETE', method, headers)
    reply = requests.delete(url + method, headers=headers)
    result = reply.json()
    if "Error" in result:
        raise Exception(result["Error"][0]["error_description"])
    return result["Response"]
