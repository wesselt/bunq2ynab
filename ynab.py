import json
import hashlib
import requests


url = 'https://api.youneedabudget.com/'


def read_file(fname):
    try:
        with open(fname, 'r') as f:
            return f.read()
    except:
        pass


def get_personal_access_token():
    token = read_file("personal_access_token.txt")
    if not token:
        raise Exception("Couldn't read YNAB personal access token.  Get one " +
            "from YNAB's developer settings and store it in " +
            "personal_access_token.txt.")
    return token.rstrip("\n")


def default_headers():
    return {
        'Authorization': 'Bearer ' + get_personal_access_token()
    }


def get(method):
    headers = default_headers()
    reply = requests.get(url + method, headers=headers)
    result = reply.json()
    if "error" in result:
        raise Exception("{0} (details: {1})".format(
                           result["error"]["name"], result["error"]["detail"]))
    return result["data"]


def post(method, data_obj):
    data = json.dumps(data_obj)
    headers = default_headers()
    print (json.dumps(data_obj, sort_keys=True, indent=2))
    print (url + method)
    reply = requests.post(url + method, headers=headers, data=data)
    result = reply.json()
    print (json.dumps(result, sort_keys=True, indent=2))
    if "error" in result:
        raise Exception("{0} (details: {1})".format(
                           result["error"]["name"], result["error"]["detail"]))
    return result
