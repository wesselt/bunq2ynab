import bunq
import sys

userid = sys.argv[1]
accountid = sys.argv[2]

method = ("v1/user/{0}/monetary-account/{1}/customer-statement?count=200"
          .format(userid, accountid))
exports = bunq.get(method)
for e in exports:
    for k, v in e.items():
        print("{0:>8}  {1}  {2}  {3}".format(
            v["id"], v["date_start"], v["date_end"], v["statement_format"]))
