import argparse
import json
import sys

import bunq

parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("bunq_user_name",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
parser.add_argument("toggle_category",
    help="Callback category to toggle (f.e. MUTATION)")
parser.add_argument("toggle_url",
    help="URL to receive the callback (f.e. https://yourdomain.com:12345)")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)


bunq_user_id = bunq.get_user_id(args.bunq_user_name)
method = "v1/user/{0}".format(bunq_user_id)
users = bunq.get(method)
for u in [u["UserPerson"] for u in users]:
    print("User: {0} ({1})".format(u["display_name"], u["id"]))
    new_notifications = []
    removed_notification = False
    for nf in u["notification_filters"]:
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
    print("Updating user...")
    data = {
        "notification_filters": new_notifications
    }
    method = "v1/user-person/{0}".format(bunq_user_id)
    users = bunq.put(method, data)
