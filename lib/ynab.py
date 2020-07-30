import datetime
import json
import os
import requests
import uuid
import sys

url = 'https://api.youneedabudget.com/'
personal_access_token_file = "personal_access_token.txt"

# 1 to log http calls, 2 to include headers
log_level = 0


# -----------------------------------------------------------------------------

def read_file(fname):
    dname = os.path.dirname(sys.argv[0])
    fn = os.path.join(dname, fname)
    if os.path.isfile(fn):
        with open(fn, 'r') as f:
            return f.read()


def get_personal_access_token():
    token = read_file(personal_access_token_file)
    if token:
        return token.rstrip("\r\n")
    raise Exception(
        "Couldn't read YNAB personal access token.  Get one " +
        "from YNAB's developer settings and store it in " +
        personal_access_token_file)


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
    if reply.headers["Content-Type"].startswith("application/json"):
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
    log_request(action, method, headers, data_obj)
    if action == 'GET':
        reply = requests.get(url + method, headers=headers)
    elif action == 'POST':
        reply = requests.post(url + method, headers=headers, data=data)
    elif action == 'PATCH':
        reply = requests.patch(url + method, headers=headers, data=data)
    log_reply(reply)
    result = reply.json()
    if "error" in result:
        raise Exception("{0} (details: {1})".format(
                           result["error"]["name"], result["error"]["detail"]))
    return result["data"]


# -----------------------------------------------------------------------------

def is_uuid(id):
    try:
        uuid.UUID("{" + id + "}")
        return True
    except ValueError as e:
        return False


def get_budget_id(budget_name):
    if is_uuid(budget_name):
        return budget_name

    reply = get('v1/budgets')
    for b in reply["budgets"]:
        if b["name"].casefold() == budget_name.casefold():
            return b["id"]
    raise Exception("YNAB budget '{0}' not found".format(budget_name))


def get_account_id(budget_id, account_name):
    if is_uuid(account_name):
        return account_name

    reply = get('v1/budgets/' + budget_id + "/accounts")
    for a in reply["accounts"]:
        if a["name"].casefold() == account_name.casefold():
            return a["id"]
    raise Exception("YNAB account '{0}' not found".format(account_name))


def get_transactions(budget_id, account_id, start_date):
    result = get("v1/budgets/{0}/accounts/{1}/transactions?since_date={2}"
        .format(budget_id, account_id, start_date))
    transactions = [t for t in result["transactions"]
        if t["payee_name"] != "Starting Balance"]
    if transactions:
        return transactions
    result = get("v1/budgets/{0}/accounts/{1}/transactions"
        .format(budget_id, account_id))
    return [t for t in result["transactions"]
        if t["payee_name"] != "Starting Balance"]


# -----------------------------------------------------------------------------

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def upload_transactions(budget_id, transactions):
    method = "v1/budgets/" + budget_id + "/transactions"
    reversed_transactions = reversed(transactions)

    new_list = [t for t in reversed_transactions if t.get("new")]
    for new_batch in chunker(new_list, 100):
        print("Creating transactions up to {}..."
              .format(new_batch[-1]["date"]))
        post(method, {"transactions": new_batch})

    patch_list = [t for t in reversed_transactions
                  if not t.get("new") and t.get("dirty")]
    for patch_batch in chunker(patch_list, 100):
        print("Patching transactions up to {}..."
              .format(patch_batch[-1]["date"]))
        patch(method, {"transactions": patch_batch})

    return len(new_list), len(patch_list)


# -----------------------------------------------------------------------------

def set_log_level(level):
    global log_level
    log_level = level


def get(method):
    return call('GET', method)


def post(method, data):
    return call('POST', method, data)


def patch(method, data):
    return call('PATCH', method, data)
