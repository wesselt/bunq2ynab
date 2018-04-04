import json
import hashlib
import requests


url = 'https://api.youneedabudget.com/'
personal_access_token_file = "personal_access_token.txt"


def read_file(fname):
    try:
        with open(fname, 'r') as f:
            return f.read()
    except:
        pass


def get_personal_access_token():
    token = read_file(personal_access_token_file)
    if token:
        return token.rstrip("\n")
    raise Exception("Couldn't read YNAB personal access token.  Get one " +
        "from YNAB's developer settings and store it in " +
        personal_access_token_file)


def call(action, method, data_obj = None):
    headers =  {
        'Authorization': 'Bearer ' + get_personal_access_token(),
        'Content-type': 'application/json'
    }
    if action == 'GET':
        reply = requests.get(url + method, headers=headers)
    elif action == 'POST':
        data = json.dumps(data_obj)
        reply = requests.post(url + method, headers=headers, data=data)
    result = reply.json()
    if "error" in result:
        raise Exception("{0} (details: {1})".format(
                           result["error"]["name"], result["error"]["detail"]))
    return result["data"]


def get(method):
    return call('GET', method)


def post(method, data):
    return call('POST', method, data)
