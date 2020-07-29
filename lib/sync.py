import datetime
from decimal import Decimal

from lib import ynab
from lib import bunq_api


def strip_descr(descr):
    if not "," in descr:
        return descr
    return ",".join(descr.split(",")[:-1])


def date_subtract(dt_str, days):
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d")
    dt = dt - datetime.timedelta(days=days)
    return dt.strftime("%Y-%m-%d")


def find_original(transactions, reversal):
    min_date = date_subtract(reversal["date"], 5)
    return next((original for original in transactions if
        "payment" in original and
        min_date <= original["date"] and
        original["date"] <= reversal["date"] and
        original["payment"]["sub_type"] == "PAYMENT" and
        original["amount"] == -reversal["amount"] and
        original["payment"]["payee"] == reversal["payment"]["payee"] and
        "Refund: " + original["payment"]["description"] ==
            reversal["payment"]["description"]
    ), None)


def find_corrected(transactions, reversal):
    return next((corrected for corrected in transactions if
        "payment" in corrected and
        corrected["date"] == reversal["date"] and
        corrected["payment"]["sub_type"] == "PAYMENT" and
        corrected["payment"]["payee"] == reversal["payment"]["payee"] and
        "Refund: " + strip_descr(corrected["payment"]["description"]) ==
            strip_descr(reversal["payment"]["description"])
     ), None)


def merge(original, reversal, corrected):
    original_cat = original.get("category_id")
    if original_cat:
        if not reversal.get("category_id"):
            print("Categorizing zerofx reversal...")
            reversal["category_id"] = original_cat
            reversal["dirty"] = True
        if not corrected.get("category_id"):
            print("Categorizing zerofx corrected...")
            corrected["category_id"] = original_cat
            corrected["dirty"] = True
    if original.get("approved"):
        if not reversal.get("approved"):
            print("Approving zerofx reversal...")
            reversal["approved"] = True
            reversal["dirty"] = True
        if not corrected.get("approved"):
            print("Approving zerofx corrected...")
            corrected["approved"] = True
            corrected["dirty"] = True


def merge_zerofx(transactions):
    # Search for payment, reversal, payment triple
    print("Merging ZeroFX duplicates...")
    for reversal in [t for t in transactions if "payment" in t]:
        if reversal["payment"]["sub_type"] == "REVERSAL":
            original = find_original(transactions, reversal)
            if not original:
                continue
            corrected = find_corrected(transactions, reversal)
            if not corrected:
                continue
            merge(original, reversal, corrected)


# -----------------------------------------------------------------------------

# Calculate occurernce for YNAB duplicate detection
def calculate_occurrence(same_day, p):
    if len(same_day) > 0 and same_day[0]["date"] != p["date"]:
        same_day.clear()
    same_day.append(p)
    return len([s for s in same_day if s["amount"] == p["amount"]])


def extend_transactions(transactions, payments, ynab_account_id):
    new_count = 0
    ynab = {}
    for t in transactions:
        ynab[t["import_id"]] = t
    same_day = []
    for p in payments:
        milliunits = int((1000 * Decimal(p["amount"])).quantize(1))
        occurrence = calculate_occurrence(same_day, p)
        import_id = "YNAB:{}:{}:{}".format(milliunits, p["date"], occurrence)
        transaction = ynab.get(import_id)
        if transaction:
            transaction["payment"] = p
        else:
            transactions.append({
                "import_id": import_id,
                "account_id": ynab_account_id,
                "date": p["date"],
                "amount": milliunits,
                "payee_name": p["payee"][:50],  # YNAB payee is max 50 chars
                "memo": p["description"][:100],  # YNAB memo is max 100 chars
                "cleared": "cleared",
                "payment": p,
                "new": True
            })

    merge_zerofx(transactions)

    return transactions


# -----------------------------------------------------------------------------

def retrieve_payments_from(transactions):
    if len(transactions) == 0:
        return "2000-01-01"
    start_dt = transactions[-1]["date"]
    min_dt_date = datetime.datetime.now() - datetime.timedelta(days=33)
    min_dt = min_dt_date.strftime("%Y-%m-%d")
    return min(start_dt, min_dt)


def synchronize(bunq_user_name, bunq_account_name,
                ynab_budget_name, ynab_account_name):

    print("Getting ynab identifiers...")
    ynab_budget_id = ynab.get_budget_id(ynab_budget_name)
    ynab_account_id = ynab.get_account_id(ynab_budget_id, ynab_account_name)

    print("Getting bunq identifiers...")
    bunq_user_id = bunq_api.get_user_id(bunq_user_name)
    bunq_account_id = bunq_api.get_account_id(bunq_user_id, bunq_account_name)

    print("Reading ynab transactions...")
    transactions = ynab.get_transactions(ynab_budget_id, ynab_account_id)
    print("Retrieved {} ynab transactions...".format(len(transactions)))

    start_dt = retrieve_payments_from(transactions)
    print("Reading bunq payments from {}...".format(start_dt))
    payments = bunq_api.get_payments(bunq_user_id, bunq_account_id, start_dt)
    print("Retrieved {} bunq payments...".format(len(payments)))

    extend_transactions(transactions, payments, ynab_account_id)

    created, patched = ynab.upload_transactions(ynab_budget_id, transactions)
    print("Created {} and patched {} transactions.".format(
        created, patched))
