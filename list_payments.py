import argparse
import json
import sys

import bunq


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("bunq_user_name",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
parser.add_argument("bunq_account_name",
    help="Bunq account name (retrieve using 'python3 list_user.py')")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)


bunq_user_id = bunq.get_user_id(args.bunq_user_name)
bunq_account_id = bunq.get_account_id(bunq_user_id, args.bunq_account_name)

method = ("v1/user/{0}/monetary-account/{1}/payment?count=24"
          .format(bunq_user_id, bunq_account_id))
payments = bunq.get(method)
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
