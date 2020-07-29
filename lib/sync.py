import datetime
from decimal import Decimal
from pprint import pprint

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


def find_original(transactions, i):
    r = transactions[i]
    rp = r["payment"]
    min_date = date_subtract(r["date"], 4)
    while True:
        i = i - 1
        if i < 0:
            return None
        o = transactions[i]
        if o["date"] < min_date:
            return None
        op = o.get("payment")
        if (not op or
            op["sub_type"].upper() != "PAYMENT" or
            o["amount"] != -r["amount"] or
            op["payee"] != rp["payee"] or
            "Refund: " + op["description"] != rp["description"]):
            continue
        return o


def find_corrected(transactions, i):
    r = transactions[i]
    rp = r["payment"]
    r_descr = strip_descr(rp["description"])
    pprint("Finding corrected of")
    pprint(rp)
    while True:
        i = i + 1
        if i == len(transactions):
            return None
        c = transactions[i]
        if c["date"] != r["date"]:
            pprint("Past date of reversal")
            pprint(c)
            return None
        cp = c.get("payment")
        if (not cp or
            cp["sub_type"].upper() != "PAYMENT" or
            cp["payee"] != rp["payee"] or
            "Refund: " + strip_descr(cp["description"]) != r_descr):
            pprint("Skipping corrected candidate")
            pprint(cp)
            continue
        return c


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
            reversal["approved"] = True
            reversal["dirty"] = True
        if not corrected.get("approved"):
            corrected["approved"] = True
            corrected["dirty"] = True


def merge_zerofx(transactions):
    pprint(transactions)
    # Search for payment, reversal, payment triple
    print("Merging ZeroFX duplicates...")
    for i in range(0, len(transactions)):
        reversal = transactions[i]
        rp = reversal.get("payment")
        if rp and rp.get("sub_type") == "REVERSAL":
            original = find_original(transactions, i)
            if not original:
                print("Didn't find original:")
                pprint(reversal)
                continue
            pprint("Original = ")
            pprint(original)
            corrected = find_corrected(transactions, i)
            if not corrected:
                print("Didn't find corrected:")
                pprint(reversal)
                continue
            pprint("Corrected = ")
            pprint(original)
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
        milliunits = str((1000 * Decimal(p["amount"])).quantize(1))
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
