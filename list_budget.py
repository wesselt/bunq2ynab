from decimal import Decimal

from lib import ynab
from lib.config import config


config.load()


def print_accounts(b):
    for a in b["accounts"]:
        if a["deleted"]:
            continue
        balance = Decimal(a["balance"])/Decimal(1000)
        print("  {0:10,}  {1:<50} ({2})".format(
            balance, a["name"], a["type"]))
        # print("  {0:<25}  account id: {1}".format("", a["id"]))


result = ynab.get("v1/budgets?include_accounts=true")
for b in result["budgets"]:
    print('Accounts for budget "{0}":'.format(b["name"]))
    print_accounts(b)
