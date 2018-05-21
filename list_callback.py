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


users = bunq.get("v1/user")
for u in users:
    for k, v in u.items():
        print('{0} "{1}"'.format(k, v["display_name"]))
        for nf in v["notification_filters"]:
            print('  {0:35} {1:10} {2}'.format(
              nf["category"],
              nf["notification_delivery_method"],
              nf.get("notification_target", "-")))
