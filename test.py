import csv
import datetime
from decimal import Decimal
import sys

import ynab


ynab_budget_id = "ea031993-e522-4a24-ad7c-f0dd3ff3a0d1"
ynab_account_id = "d4b87555-e43f-444a-a5f2-8b59afec4105"

data = {
  "transaction": {
    "account_id": ynab_account_id,
    "amount": "12340",
    "cleared": "cleared",
    "date": "2018-04-02",
    "import_id": "YNAB:12340:2018-04-02:1",
    "memo": ""
  }
}

print ("Uploading transactions to YNAB...")
method = "v1/budgets/" + ynab_budget_id + "/transactions"
result = ynab.post(method, data)
stats = result["bulk"]
print ("Uploaded {0} new and {1} duplicate transactions.".format(
       len(stats["transaction_ids"]), len(stats["duplicate_import_ids"])))
