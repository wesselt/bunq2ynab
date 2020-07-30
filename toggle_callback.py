import argparse
import json
import sys

from lib import bunq
from lib import bunq_api


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("--single-ip", action="store_true",
    help="Register BUNQ device-server with a single IP address instead " +
         "of a wildcard for all IPs.  Useful if you have a fixed IP.")
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
bunq.set_single_ip(args.single_ip)


def update_notifications(nfs):
    new_notifications = []
    removed_notification = False
    for nfi in nfs:
        for nf in nfi.values():
            if (nf["category"] == args.toggle_category and
                    nf.get("notification_target", None) == args.toggle_url):
                print("Removing callback...")
                removed_notification = True
            else:
                new_notifications.append({
                    "category": nf["category"],
                    "notification_target": nf["notification_target"]
                })

    if not removed_notification:
        print("Adding callback...")
        new_notifications.append({
            "category": args.toggle_category,
            "notification_target": args.toggle_url,
        })
    return new_notifications


bunq_user_id = bunq_api.get_user_id(args.bunq_user_name)
if args.bunq_account_name:
    bunq_account_id = bunq_api.get_account_id(bunq_user_id,
                                              args.bunq_account_name)
    method = ("v1/user/" + bunq_user_id + "/monetary-account/" +
              bunq_account_id + "/notification-filter-url")
    old_nfs = bunq.get(method)
    new_nfs = update_notifications(old_nfs)
    bunq.post(method, {"notification_filters": new_nfs})
else:
    method = "v1/user/" + bunq_user_id + "/notification-filter-url"
    old_nfs = bunq.get(method)
    new_nfs = update_notifications(old_nfs)
    bunq.post(method, {"notification_filters": new_nfs})
