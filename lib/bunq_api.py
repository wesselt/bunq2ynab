from lib import bunq
from lib.log import log

# ----- Adding a callback to the bunq account

def add_callback(bunq_user_id, bunq_account_id, url_end, url):
    log.info("Adding BUNQ callback to: {}".format(url))
    set_callbacks(bunq_user_id, bunq_account_id, url_end, [{
        "category": "MUTATION",
        "notification_target": url
    }])


def remove_callback(bunq_user_id, bunq_account_id, url_end):
    set_callbacks(bunq_user_id, bunq_account_id, url_end, [])


def set_callbacks(bunq_user_id, bunq_account_id, url_end, new_nfs):
    if not bunq_user_id or not bunq_user_id:
        raise Exception("Can't change callbacks without user and account id.")

    old_nfs = get_callbacks(bunq_user_id, bunq_account_id)
    for nfi in old_nfs:
        for nf in nfi.values():
            if (nf["category"] == "MUTATION" and
                    nf["notification_target"].endswith(url_end)):
                log.info("Removing callback...")
            else:
                new_nfs.append({
                    "category": nf["category"],
                    "notification_target": nf["notification_target"]
                })
    put_callbacks(bunq_user_id, bunq_account_id, new_nfs)


# -----------------------------------------------------------------------------

def get_user_id(user_name):
    for u in bunq.get('v1/user'):
        for k, v in u.items():
            if (v["display_name"].casefold() == user_name.casefold() or
                    str(v["id"]) == user_name):
                return str(v["id"])
    raise Exception("BUNQ user '{0}' not found".format(user_name))


def get_account_id(user_id, account_name):
    reply = bunq.get('v1/user/{0}/monetary-account'.format(user_id))
    for entry in reply:
        account_type = next(iter(entry))
        account = entry[account_type]
        if (account["status"] == "ACTIVE" and
            (account["description"].casefold() == account_name.casefold() or
                str(account["id"]) == account_name)):
            return str(account["id"])
    raise Exception("BUNQ account '{0}' not found".format(account_name))


# {"UserPerson": {...}}   -->   {...}
def first_value(data):
    return next(iter(data.values()))


def get_accounts_for_user(u):
    method = "v1/user/{}/monetary-account".format(u["id"])
    for a in [first_value(a) for a in bunq.get(method)]:
        if a["status"] == "ACTIVE":
            iban = [a["value"] for a in a["alias"] if a["type"] =="IBAN"][0]
            yield {
                "bunq_user_id": u["id"],
                "bunq_user_name": u["display_name"],
                "bunq_account_id": a["id"],
                "bunq_account_name": a["description"],
                "iban": iban
            }


def get_accounts():
    for u in [first_value(u) for u in bunq.get("v1/user")]:
        if u["status"] == "ACTIVE":
            yield from get_accounts_for_user(u)


def get_callbacks(user_id, account_id):
    method = ("v1/user/{}/monetary-account/{}/notification-filter-url"
              .format(user_id, account_id))
    return bunq.get(method)


def put_callbacks(user_id, account_id, new_notifications):
    data = {
         "notification_filters": new_notifications
    }
    method = ("v1/user/{}/monetary-account/{}/notification-filter-url"
              .format(user_id, account_id))
    bunq.post(method, data)


def map_payments(result):
    raw_payments = [p["Payment"] for p in result]
    payments = map(lambda p: {
            "amount": p["amount"]["value"],
            "date": p["created"][:10],
            "type": p["type"],
            "sub_type": p["sub_type"],
            "iban": p["counterparty_alias"]["iban"],
            "payee": p["counterparty_alias"]["display_name"],
            "description": p["description"].strip()
        }, raw_payments)
    return list(payments)


def get_payments(user_id, account_id, start_date):
    method = ("v1/user/{0}/monetary-account/{1}/payment?count=200"
              .format(user_id, account_id))
    payments = map_payments(bunq.get(method))
    if not payments:
        log.info("No bunq payments found...")
        return []
    got_date = payments[-1]["date"]
    log.info("Retrieved back to {}...".format(got_date))
    while bunq.has_previous() and start_date <= got_date:
        payments.extend(map_payments(bunq.previous()))
        got_date = payments[-1]["date"]
        log.info("Retrieved back to {}...".format(got_date))
    # For correct duplicate calculation, return only complete days
    return [p for p in payments if start_date <= p["date"]]
