import bunq
import sys

userid = sys.argv[1]
accountid = sys.argv[2]


def delete_export(exportid):
    method = "v1/user/{0}/monetary-account/{1}/customer-statement/{2}".format(
             userid, accountid, exportid)
    bunq.delete(method)


method = ("v1/user/{0}/monetary-account/{1}/customer-statement?count=200"
          .format(userid, accountid))
exports = bunq.get(method)
delete_count = 0
for e in exports:
    for k, v in e.items():
        print("Deleting export {0} ({1} > {2} {3})...".format(
            v["id"], v["date_start"], v["date_end"], v["statement_format"]))
        delete_export(v["id"])
        delete_count += 1
print("Deleted {0} exports".format(delete_count))
