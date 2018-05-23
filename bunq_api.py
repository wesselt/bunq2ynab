import bunq


def get_user_id(user_name):
    for u in bunq.get('v1/user'):
        for k, v in u.items():
            if (v["display_name"].casefold() == user_name.casefold() or
                    str(v["id"]) == user_name):
                return str(v["id"])
    raise Exception("BUNQ user '{0}' not found".format(user_name))


def get_account_id(user_id, account_name):
    reply = bunq.get('v1/user/' + user_id + '/monetary-account')
    for a in [a["MonetaryAccountBank"] for a in reply]:
        if (a["description"].casefold() == account_name.casefold() or
                str(a["id"]) == account_name):
            return str(a["id"])
    raise Exception("BUNQ account '{0}' not found".format(account_name))
