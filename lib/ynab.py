import datetime
from decimal import Decimal
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


# -----------------------------------------------------------------------------

def strip_descr(descr):
    if not "," in descr:
        return descr
    return ",".join(descr.split(",")[:-1])


def date_subtract(dt_str, days):
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d")
    dt = dt - datetime.timedelta(days=days)
    return dt.strftime("%Y-%m-%d")


def find_original(payments, i):
    a = payments[i]
    min_date = date_subtract(a["date"], 4)
    while True:
        i = i - 1
        if i < 0:
            return None
        b = payments[i]
        if b["date"] < min_date:
            return None
        if (b["sub_type"].upper() != "PAYMENT" or
            Decimal(b["amount"]) != -Decimal(a["amount"]) or
            b["payee"] != a["payee"] or
            "Refund: " + b["description"] != a["description"]):
            continue
        return b


def find_corrected(payments, i):
    a = payments[i]
    a_descr = strip_descr(a["description"])
    while True:
        i = i + 1
        if i == len(payments):
            return None
        b = payments[i]
        if b["date"] != a["date"]:
            return None
        if (b["sub_type"].upper() != "PAYMENT" or
            b["payee"] != a["payee"] or
            a_descr != "Refund: " + strip_descr(b["description"])):
            continue
        return b


def get_ynab_transactions(budget_id, account_id, payments):
    # Retrieve current YNAB transactions
    first_date = payments[0]["date"]
    result = get("v1/budgets/{0}/accounts/{1}/transactions?since_date={2}"
        .format(budget_id, account_id, first_date))
    ynab = {}
    for yt in result["transactions"]:
        ynab[yt["import_id"]] = yt
    print("YNAB has {0} transactions...".format(len(ynab)))
    return ynab


def merge(original, reversal, correction):
    original_cat = original["old"].get("category_id")
    if original_cat:
        if not reversal["old"].get("category_id"):
            print("Categorizing zerofx reversal...")
            reversal["transaction"]["category_id"] = original_cat
            reversal["dirty"] = True
        if not correction["old"].get("category_id"):
            print("Categorizing zerofx correction...")
            correction["transaction"]["category_id"] = original_cat
            correction["dirty"] = True
    if original["old"].get("approved"):
        if not reversal["old"].get("approved"):
            reversal["transaction"]["approved"] = True
            reversal["dirty"] = True
        if not correction["old"].get("approved"):
            correction["transaction"]["approved"] = True
            correction["dirty"] = True


def merge_zerofx(budget_id, account_id, payments):
    # Search for payment, reversal, payment triple
    print("Merging ZeroFX duplicates...")
    for i in range(0, len(payments)):
        reversal = payments[i]
        if reversal["sub_type"].upper() == "REVERSAL":
            original = find_original(payments, i)
            if not original:
                continue
            correction = find_corrected(payments, i)
            if not correction:
                continue
            merge(original, reversal, correction)


# -----------------------------------------------------------------------------

def upload_payments(budget_id, account_id, payments):
    if len(payments) == 0:
        return
    transactions = []
    new_count = 0
    ynab = get_ynab_transactions(budget_id, account_id, payments)
    for p in payments:
        milliunits = str((1000 * Decimal(p["amount"])).quantize(1))
        # Calculate import_id for YNAB duplicate detection
        occurrence = 1 + len([y for y in transactions
                      if y["amount"] == milliunits and y["date"] == p["date"]])
        import_id = "YNAB:{}:{}:{}".format(milliunits, p["date"], occurrence)
        old_transaction = ynab.get(import_id)
        p["transaction"] = {
            "import_id": import_id,
            "account_id": account_id,
        }
        p["dirty"] = False
        if old_transaction:
            p["old"] = old_transaction
        else:
            new_count = new_count + 1
            p["old"] = {}
            p["transaction"].update({
                "date": p["date"],
                "amount": milliunits,
                "payee_name": p["payee"][:50],  # YNAB payee is max 50 chars
                "memo": p["description"][:100],  # YNAB memo is max 100 chars
                "cleared": "cleared",
            })

    merge_zerofx(budget_id, account_id, payments)

    method = "v1/budgets/" + budget_id + "/transactions"
    new_list = [p["transaction"] for p in payments if len(p["old"]) == 0]
    if new_list:
        print("Creating {} transactions...".format(len(new_list)))
        post(method, {"transactions": new_list})

    patch_list = [p["transaction"] for p in payments
                  if len(p["old"]) > 0 and p["dirty"]]
    if patch_list:
        print("Patching {} transactions...".format(len(patch_list)))
        patch(method, {"transactions": patch_list})


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
