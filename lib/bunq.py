import base64
from OpenSSL import crypto
import json
import os
import requests
import socket
import sys

from lib import network


url = "https://api.bunq.com/"

# User-created file with the BUNQ API key
api_token_file = "api_token.txt"

# Files that store BUNQ installation and session state
private_key_file = "private_key.txt"
installation_token_file = "installation_token.txt"
session_token_file = "session_token.txt"

# 1 to log http calls, 2 to include headers
log_level = 0

# IP to limit device-server to
single_ip = False

# Pagination
older_url = None


# -----------------------------------------------------------------------------

def fname_to_path(fname):
    dname = os.path.dirname(sys.argv[0])
    return os.path.join(dname, fname)


def read_file(fname):
    fn = fname_to_path(fname)
    if os.path.isfile(fn):
        with open(fn, 'r') as f:
            return f.read()


def write_file(fname, data):
    with open(fname_to_path(fname), 'w') as f:
        f.write(data)


def delete_file(fname):
    fn = fname_to_path(fname)
    if os.path.isfile(fn):
        print("Deleting file {0}...".format(fname))
        os.unlink(fn)


def get_modification_time(fname):
    fn = fname_to_path(fname)
    if os.path.isfile(fn):
        return os.path.getmtime(fn)


def delete_old(fname, depends_on_fnames):
    my_time = get_modification_time(fname)
    if not my_time:
        return
    for depends_on in depends_on_fnames:
        their_time = get_modification_time(depends_on)
        if their_time and my_time < their_time:
            print("File {0} should not be older than {1}, removing...".format(
                fname, depends_on))
            delete_file(fname)
            return


# -----------------------------------------------------------------------------

def get_api_token():
    token = read_file(api_token_file)
    if token:
        return token.rstrip("\r\n")
    raise Exception("BUNQ API key not found.  Add an API key " +
                    "using the app and store it in " + api_token_file)


def get_private_key():
    delete_old(private_key_file, [api_token_file])
    pem_str = read_file(private_key_file)
    if pem_str:
        return crypto.load_privatekey(crypto.FILETYPE_PEM, pem_str)
    print("Generating new private key...")
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    write_file(private_key_file, pem.decode("utf-8"))
    return key


def get_public_key():
    private_key = get_private_key()
    pem = crypto.dump_publickey(crypto.FILETYPE_PEM, private_key)
    return crypto.load_publickey(crypto.FILETYPE_PEM, pem)


def get_installation_token():
    delete_old(installation_token_file, [api_token_file, private_key_file])
    token = read_file(installation_token_file)
    if token:
        return token.rstrip("\r\n")
    print("Requesting installation token...")
    public_key = get_public_key()
    pem = crypto.dump_publickey(crypto.FILETYPE_PEM, public_key)
    method = "v1/installation"
    data = {
        "client_public_key": pem.decode("utf-8")
    }
    reply = post(method, data)
    installation_token = None
    for row in reply:
        if "Token" in row:
            installation_token = row["Token"]["token"]
    if not installation_token:
        raise Exception("No token returned by installation")
    write_file(installation_token_file, installation_token)
    register_device()
    return installation_token


def register_device():
    permitted_ips = ['*']
    if single_ip:
        permitted_ips = [network.get_public_ip()]
    print("Registering permitted IPs {}".format(",".join(permitted_ips)))
    method = "v1/device-server"
    data = {
        "description": "bunq2ynab on " + network.get_hostname(),
        "secret": get_api_token(),
        "permitted_ips": permitted_ips
    }
    post(method, data)


def get_session_token():
    delete_old(session_token_file, [api_token_file, private_key_file,
               installation_token_file])
    token = read_file(session_token_file)
    if token:
        return token.rstrip("\r\n")
    print("Requesting session token...")
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
    if not (method.startswith("v1/device-server") or
            method.startswith("v1/session-server")):
        headers['X-Bunq-Client-Authentication'] = get_session_token()
        return
    headers['X-Bunq-Client-Authentication'] = get_installation_token()
    # Device-server and session-server must be signed
    private_key = get_private_key()
    sig = crypto.sign(private_key, data, 'sha256')
    sig_str = base64.b64encode(sig).decode("utf-8")
    headers['X-Bunq-Client-Signature'] = sig_str


# -----------------------------------------------------------------------------

def log_request(action, method, headers, data):
    if log_level < 1:
        return
    print("******************************")
    print("{0} {1}".format(action, method))
    if log_level > 1:
        for k, v in headers.items():
            print("  {0}: {1}".format(k, v))
    if data:
        print("-----")
        print(json.dumps(data, indent=2))
        print("-----")


def log_reply(reply):
    if log_level < 1:
        return
    print("Status: {0}".format(reply.status_code))
    if log_level > 1:
        for k, v in reply.headers.items():
            print("  {0}: {1}".format(k, v))
    print("----------")
    if reply.headers["Content-Type"] == "application/json":
        print(json.dumps(reply.json(), indent=2))
    else:
        print(reply.text)
    print("******************************")


def call_requests(action, method, data_obj):
    data = json.dumps(data_obj) if data_obj else ''
    headers = {
        'Cache-Control': 'no-cache',
        'User-Agent': 'bunq2ynab',
    }
    sign(action, method, headers, data)
    log_request(action, method, headers, data_obj)
    if action == "GET":
        reply = requests.get(url + method, headers=headers)
    elif action == "POST":
        reply = requests.post(url + method, headers=headers, data=data)
    elif action == "PUT":
        reply = requests.put(url + method, headers=headers, data=data)
    elif action == "DELETE":
        reply = requests.delete(url + method, headers=headers)
    log_reply(reply)
    if reply.headers["Content-Type"] == "application/json":
        return reply.json()
    return reply.text


def call(action, method, data=None):
    result = call_requests(action, method, data)
    if isinstance(result, str):
        return result
    if ("Error" in result and
            result["Error"][0]["error_description"]
            == "Insufficient authorisation."):
        delete_file(session_token_file)
        result = call_requests(action, method, data)
        if isinstance(result, str):
            return result
    if "Error" in result:
        raise Exception(result["Error"][0]["error_description"])
    global older_url
    older_url = result.get("Pagination", {}).get("older_url")
    return result["Response"]


# -----------------------------------------------------------------------------

def set_single_ip(value):
    global single_ip
    print(value)
    single_ip = value


def set_log_level(level):
    global log_level
    log_level = level


def get(method):
    return call('GET', method)


def has_previous():
    return older_url is not None


def previous():
    if not older_url:
        return []
    return call('GET', older_url.lstrip("/"))


def post(method, data):
    return call('POST', method, data)


def put(method, data):
    return call('PUT', method, data)


def delete(method):
    return call('DELETE', method)
