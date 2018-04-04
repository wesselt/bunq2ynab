import base64
from OpenSSL import crypto
import json
import os
import requests
import socket
import sys


url = "https://api.bunq.com/"

# Endpoint to determine our public facing IP for device-server
target_host = "api.bunq.com"
target_port = 443  # https port

# User-created file with the BUNQ API key
api_token_file = "api_token.txt"

# Files that store BUNQ installation and session state
private_key_file = "private_key.txt"
installation_token_file = "installation_token.txt"
server_public_file = "server_public.txt"
session_token_file = "session_token.txt"


# -----------------------------------------------------------------------------

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
    if os.path.isfile(fname):
        os.unlink(fname)


# -----------------------------------------------------------------------------

def get_api_token():
    token = read_file(api_token_file)
    if token:
        return token.rstrip("\n")
    raise Exception("BUNQ API key not found.  Add an API key " +
                    "using the app and store it in " + api_token_file)


def get_private_key():
    pem_str = read_file(private_key_file)
    if pem_str:
        return crypto.load_privatekey(crypto.FILETYPE_PEM, pem_str)
    print ("Generating new private key...")
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    remove_file(installation_token_file);
    remove_file(server_public_file);
    remove_file(session_token_file);
    write_file(private_key_file, pem.decode("utf-8"))
    return key


def get_public_key():
    private_key = get_private_key()
    pem = crypto.dump_publickey(crypto.FILETYPE_PEM, private_key)
    return crypto.load_publickey(crypto.FILETYPE_PEM, pem)


def get_server_public():
    pem_str = read_file(server_public_file)
    if pem_str:
        return crypto.load_publickey(crypto.FILETYPE_PEM, pem_str)
    raise Exception("Server public key not found.  This should have been " +
        "stored in " + server_public_file + " while storing the " +
        "installation token.")


def get_installation_token():
    token = read_file(installation_token_file)
    if token:
        return token.rstrip("\n")
    print ("Requesting installation token...")
    public_key = get_public_key()
    pem = crypto.dump_publickey(crypto.FILETYPE_PEM, public_key)
    method = "v1/installation"
    data = {
        "client_public_key": pem.decode("utf-8")
    }
    reply = post(method, data)
    installation_token = server_public = None
    for row in reply:
        if "Token" in row:
            installation_token = row["Token"]["token"]
        elif "ServerPublicKey" in row:
            server_public = row["ServerPublicKey"]["server_public_key"]
    if not installation_token:
        raise Exception("No token returned by installation")
    if not server_public:
        raise Exception("No server public key returned by installation")
    write_file(installation_token_file, installation_token)
    write_file(server_public_file, server_public)
    register_device()
    return installation_token


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((target_host, target_port))
        return s.getsockname()[0]


def register_device():
    ip = get_local_ip()
    print ("Registering IP " + ip)
    method = "v1/device-server"
    data = {
        "description": "bunq2ynab on " + socket.getfqdn(),
        "secret": get_api_token(),
        "permitted_ips": [ip]
    }
    post(method, data)


def get_session_token():
    token = read_file(session_token_file)
    if token:
        return token.rstrip("\n")
    print ("Requesting session token...")
    method = "v1/session-server"
    data = {
        "secret": get_api_token()
    }
    reply = post(method, data)
    session_token = None
    for row in reply:
        if "Token" in row:
            session_token = row["Token"]["token"]
    if not session_token:
        raise Exception("No token returned by session-server")
    write_file(session_token_file, session_token)
    return session_token


# -----------------------------------------------------------------------------

def sign(action, method, headers, data):
    # Installation requests are not signed
    if method.startswith("v1/installation"):
        return
    # device-server and session-server use the installation token
    # Other endpoints use a session token
    if (method.startswith("v1/device-server") or 
        method.startswith("v1/session-server")):
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


def verify(method, code, headers, data):
    # Installation responses are not signed
    if method.startswith("v1/installation"):
        return
    # Insufficient authentication errors are not signed
    if headers["Content-Type"] == "application/json":
        result = json.loads(data)
        if ("Error" in result and result["Error"][0]["error_description"] == 
                                               "Insufficient authentication."):
            return
    ciphertext = str(code) + "\n"
    for name in sorted(headers.keys()):
        if name.startswith("X-Bunq-") and name != "X-Bunq-Server-Signature":
            ciphertext += name + ": " + headers[name] + "\n"
    ciphertext += "\n" + data
    server_public = get_server_public()
    x509 = crypto.X509()
    x509.set_pubkey(server_public)
    sig_str = headers["X-Bunq-Server-Signature"]
    sig = base64.b64decode(sig_str)
    # Raises an exception when verification fails
    crypto.verify(x509, sig, ciphertext, 'sha256')


def call_requests(action, method, data_obj):
    data = ''
    if data_obj:
        data = json.dumps(data_obj)
    headers = {
        'Cache-Control': 'no-cache',
        'User-Agent': 'bunq2ynab',
        'X-Bunq-Client-Request-Id': '0',
        'X-Bunq-Geolocation': '0 0 0 0 NL',
        'X-Bunq-Language': 'en_US',
        'X-Bunq-Region': 'nl_NL'
    }
    sign(action, method, headers, data)
    if action == "GET":
        reply = requests.get(url + method, headers=headers)
    elif action == "POST":
        reply = requests.post(url + method, headers=headers, data=data)
    elif action == "DELETE":
        reply = requests.delete(url + method, headers=headers)
    verify(method, reply.status_code, reply.headers, reply.text)
    return reply


def call(action, method, data = None):
    reply = call_requests(action, method, data)
    if reply.headers["Content-Type"] != "application/json":
        return reply.text
    result = reply.json()
    if ("Error" in result and result["Error"][0]["error_description"] == 
                                               "Insufficient authentication."):
       delete_file(session_token_file)
       reply = call_requests(action, method, data)
       result = reply.json()
    if reply.headers["Content-Type"] != "application/json":
       return reply.text
    if "Error" in result:
        raise Exception(result["Error"][0]["error_description"])
    return result["Response"]
 

# -----------------------------------------------------------------------------

def get(method):
    return call('GET', method)


def post(method, data):
    return call('POST', method, data)


def delete(method):
    return call('DELETE', method)
