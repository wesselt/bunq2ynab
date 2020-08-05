import datetime
import json
import os
import requests
import uuid
import sys

from lib.config import config


url = 'https://api.youneedabudget.com/'


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
    if reply.headers["Content-Type"].startswith("application/json"):
        print(json.dumps(reply.json(), indent=2))
    else:
        print(reply.text)
    print("******************************")


def call(action, method, data_obj=None):
    data = json.dumps(data_obj) if data_obj else ''
    headers = {
        'Authorization': 'Bearer ' + config.get("personal_access_token"),
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


def get_accounts():
    result = get("v1/budgets?include_accounts=true")
    for b in result["budgets"]:
        for a in b["accounts"]:
            if not a["deleted"]:
                yield {
                    "ynab_budget_id": b["id"],
                    "ynab_budget_name": b["name"],
                    "ynab_account_id": a["id"],
                    "ynab_account_name": a["name"],
                    "transfer_payee_id": a["transfer_payee_id"]
                } 


def get_transactions(budget_id, account_id, start_date):
    result = get("v1/budgets/{0}/accounts/{1}/transactions?since_date={2}"
        .format(budget_id, account_id, start_date))
    if result["transactions"]:
        return result["transactions"]
    result = get("v1/budgets/{0}/accounts/{1}/transactions"
        .format(budget_id, account_id))
    return result["transactions"]


# -----------------------------------------------------------------------------

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def upload_transactions(budget_id, transactions):
    method = "v1/budgets/" + budget_id + "/transactions"
    reversed_transactions = list(reversed(transactions))
    created = duplicates = patched = 0

    new_list = [t for t in reversed_transactions if t.get("new")]
    for new_batch in chunker(new_list, 100):
        print("Creating transactions up to {}..."
              .format(new_batch[-1]["date"]))
        new_result = post(method, {"transactions": new_batch})
        created += len(new_result["transaction_ids"])
        duplicates += len(new_result["duplicate_import_ids"])

    patch_list = [t for t in reversed_transactions
                  if not t.get("new") and t.get("dirty")]
    for patch_batch in chunker(patch_list, 100):
        print("Patching transactions up to {}..."
              .format(patch_batch[-1]["date"]))
        patch_result, patch(method, {"transactions": patch_batch})
        patched += len(patch_result["transaction_ids"])

    return created, duplicates, patched


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
