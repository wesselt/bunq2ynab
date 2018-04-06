import bunq
import json
import sys

userid = sys.argv[1]
accountid = sys.argv[2]

method = ("v1/user/{0}/monetary-account/{1}/payment?count=24"
          .format(userid, accountid))
payments = bunq.get(method)
for v in [p["Payment"] for p in payments]:
    print ("{0:>8} {1:3}  {2}  {3} {4}".format(
        v["amount"]["value"],
        v["amount"]["currency"],
        v["created"][:15],
        v["counterparty_alias"]["iban"],
        v["counterparty_alias"]["display_name"]
    ))
    print ("{0:14}Type: {1}/{2}  {3}".format(
        "",
        v["type"],
        v["sub_type"],
        v["description"]
     ))
