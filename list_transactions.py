import argparse
from decimal import Decimal

from lib import ynab


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("ynab_budget_name",
    help="YNAB budget name (retrieve using 'python3 list_budget.py')")
parser.add_argument("ynab_account_name",
    help="YNAB account name (retrieve using 'python3 list_budget.py')")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
ynab.set_log_level(log_level)

print("Getting YNAB identifiers...")
ynab_budget_id = ynab.get_budget_id(args.ynab_budget_name)
ynab_account_id = ynab.get_account_id(ynab_budget_id, args.ynab_account_name)


def print_transaction(t):
    print(t["import_id"])
    print("{0}  {1:10,}  {2:<25} > {3}".format(
        t["date"], Decimal(t["amount"]), t["payee_name"], t["category_name"]))


result = ynab.get("v1/budgets/{0}/accounts/{1}/transactions".format(
    ynab_budget_id, ynab_account_id))
for t in result["transactions"]:
    print_transaction(t)

