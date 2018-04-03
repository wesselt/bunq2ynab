import bunq
import sys


def print_accounts(userid):
    method = 'v1/user/{0}/monetary-account'.format(userid)
    accounts = bunq.get(method)
    for a in accounts:
        for k, v in a.items():
            print("  {0:>8}  {1:25} ({2})".format(
                                                 v["id"], v["description"], k))


users = bunq.get('v1/user')
for u in users:
    for k, v in u.items():
        print("{0:>8}  {1:25} ({2})".format(v["id"], v["display_name"], k))
        print_accounts(v["id"])
