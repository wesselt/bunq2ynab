import argparse
import json
import sys

import bunq


parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)


def print_notification_filter(e):
    nfs = e["notification_filters"]
    if not nfs:
        print("  No callbacks")
        return
    for nf in e["notification_filters"]: 
        print('  {0:35} {1:10} {2}'.format(
            nf["category"],
            nf["notification_delivery_method"],
            nf.get("notification_target", "-")))


users = bunq.get("v1/user")
for u in users:
    for k, v in u.items():
        print('{0} "{1}":'.format(k, v["display_name"]))
        print_notification_filter(v)

        method = 'v1/user/{0}/monetary-account'.format(v["id"])
        for a in [a["MonetaryAccountBank"] for a in bunq.get(method)]:
            print('{} "{}" "{}":'.format(k, v["display_name"], a["description"]))
            print_notification_filter(a)
