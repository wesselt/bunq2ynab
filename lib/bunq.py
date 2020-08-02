import base64
from OpenSSL import crypto
import json
import os
import requests
import socket
import sys

from lib import network
from lib.config import config
from lib.state import state


url = "https://api.bunq.com/"

# Pagination
older_url = None


# -----------------------------------------------------------------------------

def clear_state():
    state.set("private_key", "")
    state.set("private_key_for_api_token", "")
    state.set("installation_token", "")
    state.set("device_registered", "")
    state.set("session_token", "")


def check_api_token():
    for_api_token = state.get("private_key_for_api_token")
    if for_api_token and for_api_token != get_api_token():
        print("New API token, clearing dependent keys and tokens...")
        clear_state()


def get_api_token():
    token = config.get("api_token")
    if not token or token == "enter bunq api key here":
        raise Exception("BUNQ API key not found.  Create an API key " +
                        "using the bunq and store it in " + config.config_fn)
    return token


def get_private_key():
    pem_str = state.get("private_key")
    if pem_str:
        return crypto.load_privatekey(crypto.FILETYPE_PEM, pem_str)
    print("Generating new private key...")
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    state.set("private_key", pem.decode("utf-8"))
    state.set("private_key_for_api_token", get_api_token())
    return key


def get_public_key():
    private_key = get_private_key()
    pem = crypto.dump_publickey(crypto.FILETYPE_PEM, private_key)
    return crypto.load_publickey(crypto.FILETYPE_PEM, pem)


def get_installation_token():
    token = state.get("installation_token")
    if token:
        return token
    print("Requesting installation token...")
    public_key = get_public_key()
    pem = crypto.dump_publickey(crypto.FILETYPE_PEM, public_key)
    method = "v1/installation"
    data = {
        "client_public_key": pem.decode("utf-8")
    }
    reply = post(method, data)
    token = None
    for row in reply:
        if "Token" in row:
            token = row["Token"]["token"]
    if not token:
        raise Exception("No token returned by installation")
    state.set("installation_token", token)


def register_device():
    permitted_ips = ['*']
    if config.get("single_ip"):
        permitted_ips = [network.get_public_ip()]
    print("Registering permitted IPs {}".format(",".join(permitted_ips)))
    method = "v1/device-server"
    data = {
        "description": "bunq2ynab on " + network.get_hostname(),
        "secret": get_api_token(),
        "permitted_ips": permitted_ips
    }
    post(method, data)
    state.set("device_registered", "True")


def get_session_token():
    check_api_token()
    token = state.get("session_token")
    if token:
        return token
    if not state.get("installation_token"):
        get_installation_token()
    if not state.get("device_registered"):
        register_device()
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
    state.set("session_token", session_token)
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
    if not config.get("verbose"):
        return
    print("******************************")
    print("{0} {1}".format(action, method))
    if config.get("verboseverbose"):
        for k, v in headers.items():
            print("  {0}: {1}".format(k, v))
    if data:
        print("-----")
        print(json.dumps(data, indent=2))
        print("-----")


def log_reply(reply):
    if not config.get("verbose"):
        return
    print("Status: {0}".format(reply.status_code))
    if config.get("verboseverbose"):
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
        set("session_token", "")
        result = call_requests(action, method, data)
        if isinstance(result, str):
            return result
    if "Error" in result:
        raise Exception(result["Error"][0]["error_description"])
    global older_url
    older_url = result.get("Pagination", {}).get("older_url")
    return result["Response"]


# -----------------------------------------------------------------------------

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
