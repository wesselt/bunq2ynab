import sys

from lib import bunq
from lib import bunq_api
from lib import sync
from lib import ynab
from lib.config import config


config.parser.add_argument("bunq_user_name", nargs="?",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
config.parser.add_argument("bunq_account_name", nargs="?",
    help="Bunq account name (retrieve using 'python3 list_user.py')")
config.parser.add_argument("ynab_budget_name", nargs="?",
    help="YNAB budget name (retrieve using 'python3 list_budget.py')")
config.parser.add_argument("ynab_account_name", nargs="?",
    help="YNAB account name (retrieve using 'python3 list_budget.py')")
config.parser.add_argument("--all", "-a", action="store_true",
    help="Synchronize all instead of recent transactions")
config.load()

print("Getting ynab identifiers...")
ynab_budget_id = ynab.get_budget_id(config.get("ynab_budget_name"))
ynab_account_id = ynab.get_account_id(ynab_budget_id,
                                               config.get("ynab_account_name"))

print("Getting bunq identifiers...")
bunq_user_id = bunq_api.get_user_id(config.get("bunq_user_name"))
bunq_account_id = bunq_api.get_account_id(bunq_user_id,
                                               config.get("bunq_account_name"))

sync.synchronize(bunq_user_id, bunq_account_id,
                 ynab_budget_id, ynab_account_id)
