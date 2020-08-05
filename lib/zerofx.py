import datetime


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


def merge_triple(original, reversal, corrected):
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


def merge(transactions):
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
            merge_triple(original, reversal, corrected)
