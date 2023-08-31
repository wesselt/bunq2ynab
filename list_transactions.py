import datetime
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
    print("{0}  {1:10,}  {2:<25}  {3:<50} > {4}".format(
        t["date"], Decimal(t["amount"]), t["import_id"] or "", t["payee_name"],
        t["category_name"]))

dt = datetime.datetime.utcnow() - datetime.timedelta(14)
start_dt = dt.strftime("%Y-%m-%d")

result = ynab.get_transactions(ynab_budget_id, ynab_account_id, start_dt)
for t in result:
    print_transaction(t)
