import argparse
from decimal import Decimal
import sys

import bunq
import bunq_api
import ynab


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
    help="YNAB user name (retrieve using 'python3 list_budget.py')")
parser.add_argument("ynab_account_name",
    help="YNAB account name (retrieve using 'python3 list_budget.py')")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)
ynab.set_log_level(log_level)


print("Getting BUNQ identifiers...")
bunq_user_id = bunq_api.get_user_id(args.bunq_user_name)
bunq_account_id = bunq_api.get_account_id(bunq_user_id, args.bunq_account_name)

print("Reading list of payments...")
method = ("v1/user/{0}/monetary-account/{1}/payment?count=100"
          .format(bunq_user_id, bunq_account_id))
payments = bunq.get(method)

print("Getting YNAB identifiers...")
ynab_budget_id = ynab.get_budget_id(args.ynab_budget_name)
ynab_account_id = ynab.get_account_id(ynab_budget_id, args.ynab_account_name)

print("Translating payments...")
transactions = []
first_day = None
unsorted_payments = [p["Payment"] for p in payments]
payments = sorted(unsorted_payments, key=lambda p: p["created"])
for p in payments:
    amount_value = p["amount"]["value"]
    if p["amount"]["currency"] != "EUR":
        raise Exception("Non-euro payment: " + p["amount"]["currency"])
    date = p["created"][:10]
    if not first_day or date < first_day:
        first_day = date
    payee = p["counterparty_alias"]["display_name"]
    description = p["description"]

    milliunits = str((1000 * Decimal(amount_value)).quantize(1))
    # For YNAB duplicate detection
    occurrence = 1 + len([t for t in transactions
                          if t["amount"] == milliunits and t["date"] == date])

    transactions.append({
        "account_id": ynab_account_id,
        "date": date,
        "amount": milliunits,
        "payee_name": payee[:50],  # YNAB payee is max 50 chars
        "memo": description[:100],  # YNAB memo is max 100 chars
        "cleared": "cleared",
        "import_id": "YNAB:{0}:{1}:{2}".format(milliunits, date, occurrence)
    })

# Occurrence calculation is not accurate for oldest day in the list,
# so do not upload those transactions to YNAB
safe_transactions = [t for t in transactions if first_day < t["date"]]

print("Uploading transactions to YNAB...")
method = "v1/budgets/" + ynab_budget_id + "/transactions/bulk"
result = ynab.post(method, {"transactions": safe_transactions})
stats = result["bulk"]
print("Uploaded {0} new and {1} duplicate transactions.".format(
      len(stats["transaction_ids"]), len(stats["duplicate_import_ids"])))
