import csv
import datetime
from decimal import Decimal
import sys

import bunq
import ynab


bunq_userid = sys.argv[1]
bunq_accountid = sys.argv[2]
ynab_budget_id = sys.argv[3]
ynab_account_id = sys.argv[4]

print ("Creating CSV export...")
date_end = datetime.date.today()
date_start = date_end - datetime.timedelta(days=7)
data = {
    "statement_format": "CSV",
    "date_start": date_start.strftime("%Y-%m-%d"),
    "date_end": date_end.strftime("%Y-%m-%d"),
    "regional_format": "EUROPEAN"
}
method = ("v1/user/{0}/monetary-account/{1}/customer-statement"
          .format(bunq_userid, bunq_accountid))
export = bunq.post(method, data)
exportid = export[0]["Id"]["id"]
print ("Created CSV export {0}.".format(exportid))

method = ("v1/user/{0}/monetary-account/{1}/customer-statement/{2}/content"
          .format(bunq_userid, bunq_accountid, exportid))
export = bunq.get_content(method)

method = "v1/user/{0}/monetary-account/{1}/customer-statement/{2}".format(
         bunq_userid, bunq_accountid, exportid)
bunq.delete(method)
print ("Deleted export.")

print ("Parsing CSV export...")
reader = csv.DictReader(export.splitlines(), delimiter=';', quotechar='"')
transactions = []
for row in reader:
    amount = Decimal(row["Amount"].replace(",", "."))
    milliunits = str((1000 * amount).quantize(1))
    transactions.append({
        "account_id": ynab_account_id,
        "date": row["Date"],
        "amount": milliunits,
        "payee_name": row["Counterparty"],
        "memo": row["Description"],
        "import_id": "YNAB:{0}:{1}:1".format(milliunits, row["Date"])
    })

print ("Uploading transactions to YNAB...")
method = "v1/budgets/" + ynab_budget_id + "/transactions/bulk"
result = ynab.post(method, {"transactions": transactions})
stats = result["bulk"]
print ("Uploaded {0} new and {1} duplicate transactions.".format(
       len(stats["transaction_ids"]), len(stats["duplicate_import_ids"])))
