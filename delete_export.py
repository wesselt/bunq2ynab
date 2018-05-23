import argparse
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
parser.add_argument("bunq_account_name",
    help="Bunq account name (retrieve using 'python3 list_user.py')")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)


bunq_user_id = bunq_api.get_user_id(args.bunq_user_name)
bunq_account_id = bunq_api.get_account_id(bunq_user_id, args.bunq_account_name)


def delete_export(export_id):
    method = "v1/user/{0}/monetary-account/{1}/customer-statement/{2}".format(
             bunq_user_id, bunq_account_id, export_id)
    bunq.delete(method)


method = ("v1/user/{0}/monetary-account/{1}/customer-statement?count=200"
          .format(bunq_user_id, bunq_account_id))
exports = bunq.get(method)
delete_count = 0
for e in exports:
    for k, v in e.items():
        print("Deleting export {0} ({1} > {2} {3})...".format(
            v["id"], v["date_start"], v["date_end"], v["statement_format"]))
        delete_export(v["id"])
        delete_count += 1
print("Deleted {0} exports".format(delete_count))
