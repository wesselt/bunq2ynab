import argparse
from decimal import Decimal
import sys

import bunq


parser = argparse.ArgumentParser()
parser.add_argument("-v", help="Show content of JSON messages",
                    action="store_true")
parser.add_argument("-vv", help="Show JSON messages and HTTP headers",
                    action="store_true")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)


def print_accounts(userid):
    method = 'v1/user/{0}/monetary-account'.format(userid)
    for a in bunq.get(method):
        for k, v in a.items():
            print("  {}".format(k))
            print("  {0:28}  {1:10,} {2:3}  ({3})".format(
                v["description"],
                Decimal(v["balance"]["value"]),
                v["balance"]["currency"],
                v["id"]))


users = bunq.get('v1/user')
for u in users:
    for k, v in u.items():
        print('{0} "{1}" ({2})'.format(k, v["display_name"], v["id"]))
        print_accounts(v["id"])
