from decimal import Decimal

import ynab


def print_accounts(budget_id):
    result = ynab.get("v1/budgets/" + budget_id + "/accounts")
    for a in result["accounts"]:
        balance = Decimal(a["balance"])/Decimal(1000)
        print("  {0:10,}  {1:<25} ({2})".format(
            balance, a["name"], a["type"]))
        #print("  {0:<25}  account id: {1}".format("", a["id"]))


result = ynab.get("v1/budgets")
for b in result["budgets"]:
    print('Accounts for budget "{0}":'.format(b["name"]))
    print_accounts(b["id"])
