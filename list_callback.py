import argparse
import json
import sys

import bunq
import bunq_api


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("bunq_user_name",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)


def print_notification_filter(nfs):
    if not nfs:
        print("  No callbacks")
        return
    for nfi in nfs:
        nf = nfi["NotificationFilterUrl"]
        print('  {} -> {}'.format(
            nf["category"],
            nf.get("notification_target", "-")))


bunq_user_id = bunq_api.get_user_id(args.bunq_user_name)

method = f"v1/user/{bunq_user_id}/notification-filter-url"
nfs = bunq.get(method)
print("Callbacks for user:")
print_notification_filter(nfs)

# Loop over accounts for this user
method = f"v1/user/{bunq_user_id}/monetary-account"
for acs in bunq.get(method):
    for ac in acs.values():
        account_id = ac["id"]
        print(f'Callbacks for account {account_id} "{ac["description"]}":')
        method = (f"v1/user/{bunq_user_id}/monetary-account/{account_id}/" +
                   "notification-filter-url")
        nfs = bunq.get(method)
        print_notification_filter(nfs)
