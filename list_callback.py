import bunq
import json
import sys


users = bunq.get("v1/user")
for u in users:
    for k, v in u.items():
        print('{0} "{1}"'.format(k, v["display_name"]))
        for nf in v["notification_filters"]:
            print('  {0:35} {1:10} {2}'.format(
              nf["category"],
              nf["notification_delivery_method"],
              nf.get("notification_target", "-")))
