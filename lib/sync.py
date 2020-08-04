import datetime
from decimal import Decimal

from lib import ynab
from lib import bunq_api
from lib import zerofx
from lib.config import config


class Sync:

    def __init__(self):
        self.populated = False


    def populate(self):
        print("Retrieving bunq accounts...")
        self.bunq_accounts = list(bunq_api.get_accounts())
        print("Retrieving ynab accounts...")
        self.ynab_accounts = list(ynab.get_accounts())
        self.confpairs = config.get("accounts", [])
        if not self.confpairs:
            for ba in self.bunq_accounts:
                yas = [a for a in self.ynab_accounts
                       if a["ynab_account_name"] == ba["bunq_account_name"]]
                if len(yas) == 1:
                    print("Auto matched account {}...".format(
                                                      ba["bunq_account_name"]))
                    self.confpairs.append({**ba, **yas[0]})
        self.syncpairs = [self.confpair_to_syncpair(confpair) for
            confpair in self.confpairs]

    
    def find_by_confpair(self, arr, prefix, confpair):
        name = confpair[prefix + "_name"]
        for entry in arr:
            if (entry[prefix + "_id"].casefold() == name.casefold() or
                        entry[prefix + "_name"].casefold() == name.casefold()):
                return entry


    def confpair_to_syncpair(self, confpair):
        ynab_account = next((a for a in self.ynab_accounts
            if a["ynab_account_name"].casefold() == 
                               confpair["ynab_account_name"].casefold()), None)
        if not ynab_account:
            raise Exception('YNAB doesn\'t know budget "{}" account "{}"'
                .format(confpair["ynab_budget_name"],
                        confpair["ynab_account_name"]))

        bunq_account = next((a for a in self.bunq_accounts
            if a["bunq_account_name"].casefold() == 
                               confpair["bunq_account_name"].casefold()), None)
        if not ynab_account:
            raise Exception('bunq doesn\'t know user "{}" account "{}"'
                .format(confpair["bunq_user_name"],
                        confpair["bunq_account_name"]))

        # ** is the dictionary unpack operator
        return {**ynab_account, **bunq_account}


     # Calculate occurernce for YNAB duplicate detection
    def calculate_occurrence(self, same_day, p):
        if len(same_day) > 0 and same_day[0]["date"] != p["date"]:
            same_day.clear()
        same_day.append(p)
        return len([s for s in same_day if s["amount"] == p["amount"]])


    def extend_transactions(self, transactions, payments, syncpair):
        ynab = {t["import_id"]:t for t in transactions}
        same_day = []
        for p in payments:
            milliunits = int((1000 * Decimal(p["amount"])).quantize(1))
            occurrence = self.calculate_occurrence(same_day, p)
            import_id = "YNAB:{}:{}:{}".format(milliunits, p["date"],
                                                                    occurrence)
            print("{} {} {}".format(p["payee"], p["amount"], import_id))
            transaction = ynab.get(import_id)
            if transaction:
                transaction["payment"] = p
            else:
                # YNAB payee is max 50 chars 
                new_trans = {
                    "import_id": import_id,
                    "account_id": syncpair["ynab_account_id"],
                    "date": p["date"],
                    "amount": milliunits,
                    "memo": p["description"][:100],  # YNAB memo max 100 chars
                    "cleared": "cleared",
                    "payment": p,
                    "new": True
                }
                transfer_to = next((sp for sp in self.syncpairs
                                    if sp["iban"] == p["iban"]), None)
                if transfer_to:
                    print("Detected transfer to {}...".format(
                        transfer_to["bunq_account_name"]))
                    new_trans["payee_id"] = transfer_to["transfer_payee_id"]
                else:
                    iban_descr = ""
                    if p["iban"]:
                        iban_descr = " (" + p["iban"] + ")"
                    payee_descr = p["payee"][:50-len(iban_descr)] + iban_descr
                    new_trans["payee_name"] = payee_descr
                transactions.append(new_trans)
        return transactions


    def synchronize_account(self, syncpair):
        print('Synching "{}" - "{}" to "{}" - "{}"...'.format(
            syncpair["bunq_user_name"],
            syncpair["bunq_account_name"],
            syncpair["ynab_budget_name"],
            syncpair["ynab_account_name"]))

        get_all = config.get("all", False)
        if get_all:
            start_dt = "2000-01-01"
        else:
            dt = datetime.datetime.now() - datetime.timedelta(days=35)
            start_dt = dt.strftime("%Y-%m-%d")

        print("Reading ynab transactions from {}...".format(start_dt))
        transactions = ynab.get_transactions(syncpair["ynab_budget_id"], 
                                         syncpair["ynab_account_id"], start_dt)
        print("Retrieved {} ynab transactions...".format(len(transactions)))

        # Push start date back to latest YNAB entry
        if not get_all:
            if not transactions:
                start_dt = "2000-01-01"
            else:
                last_transaction_dt = transactions[-1]["date"]
                if last_transaction_dt < start_dt:
                    start_dt = last_transaction_dt

        print("Reading bunq payments from {}...".format(start_dt))
        payments = bunq_api.get_payments(syncpair["bunq_user_id"],
                                         syncpair["bunq_account_id"], start_dt)
        print("Retrieved {} bunq payments...".format(len(payments)))

        self.extend_transactions(transactions, payments, syncpair)
        zerofx.merge(transactions)
        #created, patched = ynab.upload_transactions(syncpair["ynab_budget_id"], 
        #                                            transactions)
        #print("Created {} and patched {} transactions."
        #                                             .format(created, patched))


    def synchronize(self):
        self.populate()
        for syncpair in self.syncpairs:
           self.synchronize_account(syncpair)


sync = Sync()
