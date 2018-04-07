from decimal import Decimal
import sys

import bunq


def print_accounts(userid):
    method = 'v1/user/{0}/monetary-account'.format(userid)
    for a in [a["MonetaryAccountBank"] for a in bunq.get(method)]:
        print("  {0:28}  {1:10,} {2}".format(
            a["description"],
            Decimal(a["balance"]["value"]),
            a["balance"]["currency"]))


users = bunq.get('v1/user')
for u in users:
    for k, v in u.items():
        print('{0} "{1}"'.format(k, v["display_name"]))
        print_accounts(v["id"])
