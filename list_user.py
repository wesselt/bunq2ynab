from decimal import Decimal

from lib import bunq
from lib.config import config


config.load()


def print_accounts(userid):
    method = 'v1/user/{0}/monetary-account'.format(userid)
    for a in bunq.get(method):
        for k, v in a.items():
            print("  {0:50.50}  {1:10,} {2:3}  {3:10} {4:25.25} {5}".format(
                v["description"],
                Decimal(v["balance"]["value"]),
                v["balance"]["currency"],
                v["status"],
                k,
                v["id"]))


users = bunq.get('v1/user')
for u in users:
    for k, v in u.items():
        print('{0} "{1}" ({2})'.format(k, v.get("display_name", ''), v["id"]))
        print_accounts(v["id"])
