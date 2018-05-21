import argparse
from decimal import Decimal

import ynab


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
ynab.set_log_level(log_level)


def print_accounts(budget_id):
    result = ynab.get("v1/budgets/" + budget_id + "/accounts")
    for a in result["accounts"]:
        balance = Decimal(a["balance"])/Decimal(1000)
        print("  {0:10,}  {1:<25} ({2})".format(
            balance, a["name"], a["type"]))
        # print("  {0:<25}  account id: {1}".format("", a["id"]))


result = ynab.get("v1/budgets")
for b in result["budgets"]:
    print('Accounts for budget "{0}":'.format(b["name"]))
    print_accounts(b["id"])
