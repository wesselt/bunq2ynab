import base64
import json
import os
import requests
import socket
import sys
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from lib import network
from lib.config import config
from lib.state import state
from lib.log import log

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


def check_stale_api_token():
    for_api_token = state.get("private_key_for_api_token")
    if for_api_token and for_api_token != config.get("api_token"):
        log.warning("New API token, clearing dependent keys and tokens...")
        clear_state()


def get_private_key():
    pem_str = state.get("private_key")
    if pem_str:
        return serialization.load_pem_private_key(
            pem_str.encode('utf-8'),
            password=None
        )
    log.info("Generating new private key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    state.set("private_key", pem.decode("utf-8"))
    state.set("private_key_for_api_token", config.get("api_token"))
    return private_key


def get_public_key():
    private_key = get_private_key()
    public_key = private_key.public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode("utf-8")


def get_installation_token():
    token = state.get("installation_token")
    if token:
        return token
    log.info("Requesting installation token...")
    public_key = get_public_key()
    method = "v1/installation"
    data = {
        "client_public_key": public_key
    }
    reply = post(method, data)
    token = None
    for row in reply:
        if "Token" in row:
            token = row["Token"]["token"]
    if not token:
        raise Exception("No token returned by installation")
    state.set("installation_token", token)
    return token


def register_device():
    permitted_ips = ['*']
    if config.get("single_ip"):
        permitted_ips = [network.get_public_ip()]
    log.info("Registering permitted IPs {}".format(",".join(permitted_ips)))
    method = "v1/device-server"
    data = {
        "description": "bunq2ynab on " + network.get_hostname(),
        "secret": config.get("api_token"),
        "permitted_ips": permitted_ips
    }
    post(method, data)
    state.set("device_registered", "True")


def get_session_token():
    check_stale_api_token()
    token = state.get("session_token")
    if token:
        return token
    if not state.get("installation_token"):
        get_installation_token()
    if not state.get("device_registered"):
        register_device()
    log.info("Requesting session token...")
    method = "v1/session-server"
    data = {
        "secret": config.get("api_token")
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
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    sig_str = base64.b64encode(signature).decode("utf-8")
    headers['X-Bunq-Client-Signature'] = sig_str


# -----------------------------------------------------------------------------

def log_request(action, method, headers, data):
    log.debug("******************************")
    log.debug("{0} {1}".format(action, method))
    for k, v in headers.items():
        log.debug("  {0}: {1}".format(k, v))
    if data:
        log.debug("-----")
        log.debug(json.dumps(data, indent=2))
        log.debug("-----")


def log_reply(reply):
    log.debug("Status: {0}".format(reply.status_code))
    for k, v in reply.headers.items():
        log.debug("  {0}: {1}".format(k, v))
    log.debug("----------")
    if reply.headers["Content-Type"] == "application/json":
        log.debug(json.dumps(reply.json(), indent=2))
    else:
        log.debug(reply.text)
    log.debug("******************************")


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
    if "Error" in result:
        descr = result["Error"][0]["error_description"]
        if descr == "Insufficient authorisation.":
            state.set("session_token", "")
            result = call_requests(action, method, data)
            if isinstance(result, str):
                return result
    if "Error" in result:
        descr = result["Error"][0]["error_description"]
        if "Too many requests" in descr:
            log.debug("waiting 3 seconds...")
            time.sleep(3)
            result = call_requests(action, method, data)
            if isinstance(result, str):
                return result
    if "Error" in result:
        raise Exception(result["Error"][0]["error_description"])
    global older_url
    older_url = result.get("Pagination", {}).get("older_url")

    return result["Response"]


# -----------------------------------------------------------------------------

# Get first result set, leave pagination to caller
def fetch(method):
    return call('GET', method)


# Get all results with pagination
def get(method):
    # When no count is given, the default count is set to 10.
    # The maximum count you can set is 200.
    # https://beta.doc.bunq.com/basics/pagination
    if "count=" in method:
        raise Exception("Internal error: call to bunq.get() with count "
            f"argument.  Call fetch() instead.  Method: {method}")
    if "?" in method:
        method_count = method + "&count=200"
    else:
        method_count = method + "?count=200"
    result = call('GET', method_count)
    while has_previous():
        result.extend(previous())
    return result


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
