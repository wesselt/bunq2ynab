import argparse
from decimal import Decimal
import json
import sys

import bunq


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("source_name",
    help="Source Bunq account name (retrieve using 'python3 list_user.py')")
parser.add_argument("target_name",
    help="Target Bunq account name (retrieve using 'python3 list_user.py')")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)


def dump(data):
    print(json.dumps(data, indent=2))


def collect_user_accounts(user_id):
    accounts = []
    method = f"v1/user/{user_id}/monetary-account"
    for e in bunq.get(method):
        account_type = next(iter(e))
        a = e[account_type]
        for al in a["alias"]:
            if al["type"] == "IBAN":
                accounts.append({
                    "user_id": user_id,
                    "account_id": a["id"],
                    "description": a["description"],
                    "iban": al["value"],
                    "value": a["balance"]["value"],
                    "currency": a["balance"]["currency"],
                    "name": al["name"]
                })
    return accounts


def collect_accounts():
    accounts = []
    for u in bunq.get('v1/user'):
        for k, v in u.items():
            accounts.extend(collect_user_accounts(v['id']))
    return accounts


def find_account(accounts, name):
    for a in accounts:
        if (name.casefold() == a["description"].casefold() or
                name.casefold() == a["iban"].casefold()):
            return a



accounts = collect_accounts()
source = find_account(accounts, args.source_name)
if not source:
    print(f"No account matches source {args.source_name}")
    sys.exit(1)
target = find_account(accounts, args.target_name)
if not target:
    print(f"No account matches target {args.target_name}")
    sys.exit(1)

if Decimal(source["value"]) <= 0:
    print("There is no money in the source account")
    sys.exit(1)

# Move balance to target account
print(f"Sending {source['value']} {source['currency']} from " +
      f"{source['iban']} to {target['iban']}...")
method = (f"v1/user/{source['user_id']}/monetary-account/" +
          f"{source['account_id']}/payment")
data = {
    "amount": {
        "value": source["value"],
        "currency": source["currency"]
    },
    "counterparty_alias": {
        "type": "IBAN",
        "value": target["iban"],
        "name": target["name"]
    },
    "description": "Flushing account"
}
bunq.post(method, data)
