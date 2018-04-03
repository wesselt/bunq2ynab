import ynab


def print_accounts(budget_id):
    result = ynab.get("v1/budgets/" + budget_id + "/accounts")
    for a in result["accounts"]:
        print("  {0:<25}  {1}  balance: {2}".format(
            a["name"], a["type"], a["balance"]))
        print("  {0:<25}  account id: {1}".format("", a["id"]))


result = ynab.get("v1/budgets")
for b in result["budgets"]:
    print("{0:<25}  modified: {1}".format(
        b["name"], b["last_modified_on"][0:10]))
    print("{0:<25}  budget id: {1}".format("", b["id"]))
    print_accounts(b["id"])
