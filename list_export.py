import bunq
import sys

bunq_user_name = sys.argv[1]
bunq_account_name = sys.argv[2]

bunq_user_id = bunq.get_user_id(bunq_user_name)
bunq_account_id = bunq.get_account_id(bunq_user_id, bunq_account_name)

method = ("v1/user/{0}/monetary-account/{1}/customer-statement?count=200"
          .format(bunq_user_id, bunq_account_id))
exports = bunq.get(method)
for e in exports:
    for k, v in e.items():
        print("{0:>8}  {1}  {2}  {3}".format(
            v["id"], v["date_start"], v["date_end"], v["statement_format"]))
