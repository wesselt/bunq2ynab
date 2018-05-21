import argparse
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

method = ("v1/user/{0}/monetary-account/{1}/customer-statement?count=200"
          .format(bunq_user_id, bunq_account_id))
exports = bunq.get(method)
for e in exports:
    for k, v in e.items():
        print("{0:>8}  {1}  {2}  {3}".format(
            v["id"], v["date_start"], v["date_end"], v["statement_format"]))
