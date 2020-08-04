from decimal import Decimal

from lib import ynab
from lib.config import config


config.parser.add_argument("ynab_budget_name",
    help="YNAB budget name (retrieve using 'python3 list_budget.py')")
config.parser.add_argument("ynab_account_name",
    help="YNAB account name (retrieve using 'python3 list_budget.py')")
config.load()


print("Getting YNAB identifiers...")
ynab_budget_id = ynab.get_budget_id(config.get("ynab_budget_name"))
ynab_account_id = ynab.get_account_id(ynab_budget_id,
                                               config.get("ynab_account_name"))


def print_transaction(t):
    print("{0}  {1:10,}  {2:<50} > {3}".format(
        t["date"], Decimal(t["amount"]), t["payee_name"], t["category_name"]))


result = ynab.get("v1/budgets/{0}/accounts/{1}/transactions".format(
    ynab_budget_id, ynab_account_id))
for t in result["transactions"]:
    print_transaction(t)
