import json
import os
import requests


url = 'https://api.youneedabudget.com/'
personal_access_token_file = "personal_access_token.txt"

# 1 to log http calls, 2 to include headers
log_level = 0


# -----------------------------------------------------------------------------

def read_file(fname):
    if os.path.isfile(fname):
        with open(fname, 'r') as f:
            return f.read()


def get_personal_access_token():
    token = read_file(personal_access_token_file)
    if token:
        return token.rstrip("\r\n")
    raise Exception(
        "Couldn't read YNAB personal access token.  Get one " +
        "from YNAB's developer settings and store it in " +
        personal_access_token_file)


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


def call(action, method, data_obj=None):
    data = json.dumps(data_obj) if data_obj else ''
    headers = {
        'Authorization': 'Bearer ' + get_personal_access_token(),
        'Content-type': 'application/json'
    }
    log_request(action, method, headers, data)
    if action == 'GET':
        reply = requests.get(url + method, headers=headers)
    elif action == 'POST':
        reply = requests.post(url + method, headers=headers, data=data)
    log_reply(reply)
    result = reply.json()
    if "error" in result:
        raise Exception("{0} (details: {1})".format(
                           result["error"]["name"], result["error"]["detail"]))
    return result["data"]


# -----------------------------------------------------------------------------

def set_log_level(level):
    global log_level
    log_level = level


def get(method):
    return call('GET', method)


def post(method, data):
    return call('POST', method, data)
