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
parser.add_argument("bunq_account_name", nargs='?',
    help="Bunq account name (retrieve using 'python3 list_user.py')")
parser.add_argument("toggle_category",
    help="Callback category to toggle (f.e. MUTATION)")
parser.add_argument("toggle_url",
    help="URL to receive the callback (f.e. https://yourdomain.com:12345)")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)


def update_notifications(nfs):
    new_notifications = []
    removed_notification = False
    for nf in nfs:
        if (nf["notification_delivery_method"] == "URL" and
                nf["category"] == args.toggle_category and
                nf.get("notification_target", None) == args.toggle_url):
            print("Removing callback...")
            removed_notification = True
        else:
            # Preserve any other callback
            new_notifications.append(nf)

    if not removed_notification:
        print("Adding callback...")
        new_notifications.append({
            "category": args.toggle_category,
            "notification_delivery_method": "URL",
            "notification_target": args.toggle_url,
        })
    return new_notifications


bunq_user_id = bunq_api.get_user_id(args.bunq_user_name)
if args.bunq_account_name:
    bunq_account_id = bunq_api.get_account_id(bunq_user_id,
                                                        args.bunq_account_name)
    method = "v1/user/{}/monetary-account-bank/{}".format(
                                                 bunq_user_id, bunq_account_id)
    result = bunq.get(method)
    old_nfs = result[0]["MonetaryAccountBank"]["notification_filters"]
    new_nfs = update_notifications(old_nfs)
    bunq.put(method, {"notification_filters": new_nfs})
else:
    method = "v1/user-person/{}".format(bunq_user_id)
    result = bunq.get(method)
    old_nfs = result[0]["UserPerson"]["notification_filters"]
    new_nfs = update_notifications(old_nfs)
    bunq.put(method, {"notification_filters": new_nfs})
