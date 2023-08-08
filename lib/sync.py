import datetime
from decimal import Decimal

from lib import ynab
from lib import bunq_api
from lib import zerofx
from lib.config import config
from lib.log import log


def pair_to_str(pair):
    return '"{}" - "{}" to "{}" - "{}"'.format(
        pair["bunq_user_name"],
        pair["bunq_account_name"],
        pair["ynab_budget_name"],
        pair["ynab_account_name"])


def key_fail(key, conf, account):
    return (conf[key] != "*" and
       conf[key].casefold() != account[key].casefold()) 


def matching_pairs(bunq, ynab, conf):
    if (key_fail("bunq_user_name", conf, bunq) or
            key_fail("bunq_account_name", conf, bunq) or
            key_fail("ynab_budget_name", conf, ynab) or
            key_fail("ynab_account_name", conf, ynab)):
        return False

    # IF either account is *, th names must match
    if (conf["bunq_account_name"] == "*" or
            conf["ynab_account_name"] == "*"):
        if (bunq["bunq_account_name"].casefold() !=
                ynab["ynab_account_name"].casefold()):
            return False

    conf["matched"] = True
    return True


def get_last_transaction_date(transactions):
    for t in reversed(transactions):
        # Ignore manually entered transactions (they're uncleared)
        if (t["payee_name"] != "Starting Balance" and
                t["cleared"] != "uncleared"):
            return t["date"]
    return "2000-01-01"


class Sync:

    def __init__(self):
        self.populated = False


    def populate(self):
        if self.populated:
            raise Exception("Sync object is already populated")
        log.info("Retrieving bunq accounts...")
        self.bunq_accounts = list(bunq_api.get_accounts())
        log.info("Retrieving ynab accounts...")
        self.ynab_accounts = list(ynab.get_accounts())

        self.confpairs = config.get("accounts", [{}])
        if not isinstance(self.confpairs, list):
            raise Exception('Configuration "accounts" must be a list')
        for conf in self.confpairs:
            for k in conf:
                if k not in ("bunq_user_name", "bunq_account_name",
                             "ynab_budget_name", "ynab_account_name"):
                    raise Exception('Accounts cannot contain "{}"'.format(k))
            if conf.get("bunq_user_name", "") == "":
                conf["bunq_user_name"] = "*"
            if conf.get("bunq_account_name", "") == "":
                conf["bunq_account_name"] = "*"
            if conf.get("ynab_budget_name", "") == "":
                conf["ynab_budget_name"] = "*"
            if conf.get("ynab_account_name", "") == "":
                conf["ynab_account_name"] = "*"

        self.syncpairs = [{**ba, **ya} 
            for ba in self.bunq_accounts
            for ya in self.ynab_accounts
            if [True for cp in self.confpairs
                if matching_pairs(ba, ya, cp)]]

        for cp in self.confpairs:
            if "matched" not in cp:
                log.warning("No matches for rule {}.".format(pair_to_str(cp)))
            else:
                del cp["matched"]

        self.populated = True


    def get_bunq_user_ids(self):
        if not self.populated:
            raise Exception("Get_bunq_user_ids called before populate")
        users = set()
        for syncpair in self.syncpairs:
            users.add(syncpair["bunq_user_id"])
        return list(users)


    # Calculate occurernce for YNAB duplicate detection
    def calculate_occurrence(self, same_day, p):
        if same_day and same_day[0]["date"] != p["date"]:
            same_day.clear()
        same_day.append(p)
        return len([s for s in same_day if s["amount"] == p["amount"]])


    def extend_transactions(self, transactions, payments, syncpair):
        ynab = {t["import_id"]:t for t in transactions if t["import_id"]}
        same_day = []
        for p in payments:
            milliunits = int((1000 * Decimal(p["amount"])).quantize(1))
            occurrence = self.calculate_occurrence(same_day, p)
            import_id = "YNAB:{}:{}:{}".format(milliunits, p["date"],
                                                                    occurrence)
            transfer_to = next((sp for sp in self.syncpairs
                                if sp["iban"] == p["iban"]), None)
            transaction = ynab.get(import_id)

            # Upload a matched uncleared transaction as if it were a new
            # transaction.  This allows YNAB to match it with an
            # uncleared transaction.
            if transaction and transaction["cleared"] != "uncleared":
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
                if transfer_to:
                    new_trans["payee_id"] = transfer_to["transfer_payee_id"]
                else:
                    new_trans["payee_name"] = p["payee"][:50]
                transactions.append(new_trans)
        return transactions


    def synchronize_account(self, syncpair):
        log.info("Synching {}...".format(pair_to_str(syncpair)))

        get_all = config.get("all")
        get_start = config.get("start")
        if get_all:
            start_dt = "2000-01-01"
        elif get_start:
            start_dt = get_start
        else:
            dt = datetime.datetime.utcnow() - datetime.timedelta(days=35)
            start_dt = dt.strftime("%Y-%m-%d")

        log.info("Reading ynab transactions from {}...".format(start_dt))
        transactions = ynab.get_transactions(syncpair["ynab_budget_id"], 
                                         syncpair["ynab_account_id"], start_dt)
        log.info("Retrieved {} ynab transactions...".format(len(transactions)))

        if not get_all and not get_start:
            # Push start date back to latest uncleared YNAB entry
            start_dt = get_last_transaction_date(transactions)
            today_dt = datetime.datetime.utcnow().strftime("%Y-%m-%d")
            if today_dt < start_dt:
                # Manual clear combined with timezone can put a transaction
                # in the UTC future
                # https://github.com/wesselt/bunq2ynab/issues/46
                log.warn(f"Last YNAB transaction {start_dt} is in the future")
                start_dt = today_dt

        log.info("Reading bunq payments from {}...".format(start_dt))
        payments = bunq_api.get_payments(syncpair["bunq_user_id"],
                                         syncpair["bunq_account_id"], start_dt)
        log.info("Retrieved {} bunq payments...".format(len(payments)))

        self.extend_transactions(transactions, payments, syncpair)
        zerofx.merge(transactions)

        created, duplicates, patched = ynab.upload_transactions(
            syncpair["ynab_budget_id"], transactions)

        msg = "{}: Created {} and patched {} transactions.{}".format(
            pair_to_str(syncpair), created, patched,
            "  There were {} duplicates.".format(duplicates)
                if duplicates else "")
        log.info(msg)
        return msg


    def synchronize_iban(self, iban):
        if not self.populated:
            raise Exception("Synchronize called before populate")
        results = ""
        for syncpair in self.syncpairs:
            if syncpair["iban"] == iban:
                return self.synchronize_account(syncpair)
        msg = "No account with IBAN {}".format(iban)
        log.warning(msg)
        return msg


    def synchronize(self):
        if not self.populated:
            raise Exception("Synchronize called before populate")
        results = ""
        for syncpair in self.syncpairs:
            results += self.synchronize_account(syncpair)
        return results
