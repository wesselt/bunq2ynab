import json
import sys

from lib import bunq
from lib import bunq_api
from lib.config import config


config.parser.add_argument("bunq_account_name",
    help="Bunq account name (retrieve using 'python3 list_user.py')")
config.parser.add_argument("--count",
    help="Retrieve X transactions (up to 200)")
config.load()


def print_payments(payments):
    for v in [p["Payment"] for p in payments]:
        print("{0:>8} {1:3}  {2}  {3} {4}".format(
            v["amount"]["value"],
            v["amount"]["currency"],
            v["created"][:16],
            v["counterparty_alias"]["iban"],
            v["counterparty_alias"]["display_name"]
        ))
        print("{0:14}Type: {1}/{2}  {3}".format(
            "",
            v["type"],
            v["sub_type"],
            v["description"]
         ))


def list_payments(account):
    bunq_user_id = account["bunq_user_id"]
    bunq_account_id = account["bunq_account_id"]
    get_all = config.get("all")
    remaining = int(config.get("count") or 100)
    batch_size = 200

    method = ("v1/user/{0}/monetary-account/{1}/payment?count={2}"
              .format(bunq_user_id, bunq_account_id, batch_size))
    payments = bunq.fetch(method)
    while payments:
        remaining -= len(payments)
        if get_all or remaining > 0:
            print_payments(payments)
        else:
            print_payments(payments[:batch_size + remaining])
            break
        payments = bunq.previous()


bunq_account_name = config.get("bunq_account_name").casefold()
for a in bunq_api.get_accounts():
    if a["bunq_account_name"].casefold() == bunq_account_name:
        list_payments(a)
