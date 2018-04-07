import bunq
import sys


def print_accounts(userid):
    method = 'v1/user/{0}/monetary-account'.format(userid)
    accounts = bunq.get(method)
    for a in accounts:
        for k, v in a.items():
            print("  {0:28}  ({1})".format(v["description"], k))


users = bunq.get('v1/user')
for u in users:
    for k, v in u.items():
        print("{0:30}  ({1})".format(v["display_name"], k))
        print_accounts(v["id"])
