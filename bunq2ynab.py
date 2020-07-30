import argparse
import sys

from lib import bunq
from lib import bunq_api
from lib import sync
from lib import ynab


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("bunq_user_name",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
parser.add_argument("bunq_account_name",
    help="Bunq account name (retrieve using 'python3 list_user.py')")
parser.add_argument("ynab_budget_name",
    help="YNAB budget name (retrieve using 'python3 list_budget.py')")
parser.add_argument("ynab_account_name",
    help="YNAB account name (retrieve using 'python3 list_budget.py')")
parser.add_argument("--all", "-a", action="store_true",
    help="Synchronize all instead of recent transactions")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)
ynab.set_log_level(log_level)

print("Getting ynab identifiers...")
ynab_budget_id = ynab.get_budget_id(args.ynab_budget_name)
ynab_account_id = ynab.get_account_id(ynab_budget_id, args.ynab_account_name)

print("Getting bunq identifiers...")
bunq_user_id = bunq_api.get_user_id(args.bunq_user_name)
bunq_account_id = bunq_api.get_account_id(bunq_user_id, args.bunq_account_name)

sync.synchronize(bunq_user_id, bunq_account_id,
                 ynab_budget_id, ynab_account_id, sync_all=args.all)
