import argparse
import csv
from decimal import Decimal
import sys

from lib import ynab


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("input_file",
    help="CSV file exported from Bunq to upload to YNAB")
parser.add_argument("ynab_budget_name",
    help="YNAB user name (retrieve using 'python3 list_budget.py')")
parser.add_argument("ynab_account_name",
    help="YNAB account name (retrieve using 'python3 list_budget.py')")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
ynab.set_log_level(log_level)


print("Getting YNAB identifiers...")
ynab_budget_id = ynab.get_budget_id(args.ynab_budget_name)
ynab_account_id = ynab.get_account_id(ynab_budget_id, args.ynab_account_name)

print("Determining file type...")
with open(args.input_file, 'r') as csvfile:
    input_lines = csvfile.readlines()
if input_lines[0].startswith('"Date";'):
    delimiter = ";"
elif input_lines[0].startswith('"Date",'):
    delimiter = ","
else:
    raise Exception("Unexpected first line: " + lines[0])

print("Reading CSV with delimiter '{0}'...".format(delimiter))
reader = csv.DictReader(input_lines, delimiter=delimiter, quotechar='"')
transactions = []
first_day = None
for row in reader:
    if not first_day or row["Date"] < first_day:
        first_day = row["Date"]
    transactions.append({
        # Remove thousand separator, replace decimal separator
        # 1.000,00  -->  1000.00
        "amount": row["Amount"].replace(".", "").replace(",", "."),
        "date": row["Date"],
        "payee": row["Name"],
        "description": row["Description"]
    })

# For correct duplicate calculation, return only complete days
transactions = [t for t in transactions if first_day < t["date"]]

print("Uploading transactions to YNAB...")
stats = ynab.upload_transactions(ynab_budget_id, ynab_account_id, transactions)
print("Uploaded {0} new and {1} duplicate transactions.".format(
      len(stats["transaction_ids"]), len(stats["duplicate_import_ids"])))
