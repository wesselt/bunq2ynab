from lib import bunq


def get_user_id(user_name):
    for u in bunq.get('v1/user'):
        for k, v in u.items():
            if (v["display_name"].casefold() == user_name.casefold() or
                    str(v["id"]) == user_name):
                return str(v["id"])
    raise Exception("BUNQ user '{0}' not found".format(user_name))


def get_account_type(user_id, account_id):
    reply = bunq.get('v1/user/{0}/monetary-account/{1}'.format(
                     user_id, account_id))
    return next(iter(reply[0]))


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


def get_callbacks(user_id, account_id):
    method = ("v1/user/" + user_id + "/monetary-account/" + account_id +
              "/notification-filter-url")
    return bunq.get(method)


def put_callbacks(user_id, account_id, new_notifications):
    data = {
         "notification_filters": new_notifications
    }
    method = ("v1/user/" + user_id + "/monetary-account/" + account_id +
              "/notification-filter-url")
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
    got_date = payments[-1]["date"]
    print("Retrieved back to {}...".format(got_date))
    while bunq.has_previous() and start_date <= got_date:
        payments.extend(map_payments(bunq.previous()))
        got_date = payments[-1]["date"]
        print("Retrieved back to {}...".format(got_date))
    # For correct duplicate calculation, return only complete days
    return [p for p in payments if start_date <= p["date"]]
