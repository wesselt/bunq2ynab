from decimal import Decimal

from lib import bunq
from lib import bunq_api
from lib.config import config


config.load()


def print_accounts(u):
    for a in bunq_api.get_accounts_for_user(u):
        print("  {0:50.50}  {1:10,} {2:3}  {3:10} {4:25.25} {5}".format(
            a["bunq_account_name"],
            a["balance"],
            a["currency"],
            a["status"],
            a["type"],
            a["bunq_account_id"]))


users = bunq.get('v1/user')
for u in users:
    for k, v in u.items():
        print('{0} "{1}" ({2})'.format(k, v.get("display_name", ''), v["id"]))
        print_accounts(v)
