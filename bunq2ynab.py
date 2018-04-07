from decimal import Decimal
import sys

import bunq
import ynab


bunq_userid = sys.argv[1]
bunq_accountid = sys.argv[2]
ynab_budget_name = sys.argv[3]
ynab_account_name = sys.argv[4]

print("Reading list of payments...")
method = ("v1/user/{0}/monetary-account/{1}/payment?count=24"
          .format(bunq_userid, bunq_accountid))
payments = bunq.get(method)

print("Getting YNAB UUIDs...")
ynab_budget_id = ynab.get_budget_id(ynab_budget_name)
ynab_account_id = ynab.get_account_id(ynab_budget_id, ynab_account_name)

print("Translating payments...")
transactions = []
for p in [p["Payment"] for p in payments]:
    amount = p["amount"]["value"]
    if p["amount"]["currency"] != "EUR":
        raise Exception("Non-euro payment: " + p["amount"]["currency"])
    date = p["created"][:10]
    payee = p["counterparty_alias"]["display_name"]
    description = p["description"]

    milliunits = str((1000 * Decimal(amount)).quantize(1))
    transactions.append({
        "account_id": ynab_account_id,
        "date": date,
        "amount": milliunits,
        "payee_name": payee,
        "memo": description[:100],  # YNAB memo is max 100 chars
        "cleared": "cleared",
        "import_id": "YNAB:{0}:{1}:1".format(milliunits, date)
    })

print("Uploading transactions to YNAB...")
method = "v1/budgets/" + ynab_budget_id + "/transactions/bulk"
result = ynab.post(method, {"transactions": transactions})
stats = result["bulk"]
print("Uploaded {0} new and {1} duplicate transactions.".format(
      len(stats["transaction_ids"]), len(stats["duplicate_import_ids"])))
