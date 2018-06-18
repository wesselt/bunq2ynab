import argparse
import atexit
import socket
import subprocess
import time

import bunq_api
import ynab
import network


parser = argparse.ArgumentParser()
parser.add_argument("--port", default=44716, type=int,
    help="TCP port number to listen to")
parser.add_argument("bunq_user_name",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
parser.add_argument("bunq_account_name",
    help="Bunq account name (retrieve using 'python3 list_user.py')")
parser.add_argument("ynab_budget_name",
    help="YNAB user name (retrieve using 'python3 list_budget.py')")
parser.add_argument("ynab_account_name",
    help="YNAB account name (retrieve using 'python3 list_budget.py')")
args = parser.parse_args()


print("Getting BUNQ identifiers...")
bunq_user_id = bunq_api.get_user_id(args.bunq_user_name)
bunq_account_id = bunq_api.get_account_id(bunq_user_id, args.bunq_account_name)

print("Getting YNAB identifiers...")
ynab_budget_id = ynab.get_budget_id(args.ynab_budget_name)
ynab_account_id = ynab.get_account_id(ynab_budget_id, args.ynab_account_name)


def add_callback(port):
    public_ip = network.get_public_ip()
    if public_ip != network.get_local_ip():
        network.open_port(port)
    url = "https://{}:{}/bunq2ynab-autosync".format(public_ip, port)
    print("Adding BUNQ callback to: {}".format(url))
    set_autosync_callbacks([{
        "category": "MUTATION",
        "notification_delivery_method": "URL",
        "notification_target": url
    }])


def remove_callback():
    network.close_port()
    set_autosync_callbacks([])


def set_autosync_callbacks(new_nfs):
    old_nfs = bunq_api.get_callbacks(bunq_user_id, bunq_account_id)
    for nf in old_nfs:
       if (nf["category"] == "MUTATION" and
              nf["notification_delivery_method"] == "URL" and
              nf["notification_target"].endswith("/bunq2ynab-autosync")):
            print("Removing old callback...")
       else:
           new_nfs.append(nf)
    bunq_api.put_callbacks(bunq_user_id, bunq_account_id, new_nfs)


def sync():
    print("Reading list of payments...")
    transactions = bunq_api.get_transactions(bunq_user_id, bunq_account_id)
    print("Uploading transactions to YNAB...")
    stats = ynab.upload_transactions(ynab_budget_id, ynab_account_id,
                                     transactions)
    print("Uploaded {0} new and {1} duplicate transactions.".format(
          len(stats["transaction_ids"]), len(stats["duplicate_import_ids"])))
    print("Finished sync at " + time.strftime("%X"))
    print("")


add_callback(args.port)
atexit.register(remove_callback)

print("Listening on port {0}".format(args.port))
print("")
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('0.0.0.0', args.port))
serversocket.listen(5)
while True:
    (clientsocket, address) = serversocket.accept()
    clientsocket.close()
    print("Incoming call from {0}...".format(address[0]))
    bunq_network = "185.40.108.0/22"
    if network.addressInNetwork(address[0], bunq_network):
        try:
            sync()
        except Exception as e:
            print("An error occured: {0}".format(e))
    else:
        print("Not from BUNQ {} range, ignoring...".format(bunq_network))
