import argparse
import errno
import socket
import time

from lib import bunq
from lib import bunq_api
from lib import ynab
from lib import network


# ----- Parameters

refresh_callback_minutes = 8*60
refresh_nocallback_minutes = 60 


# ----- Parse command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("-v", action="store_true",
    help="Show content of JSON messages")
parser.add_argument("-vv", action="store_true",
    help="Show JSON messages and HTTP headers")
parser.add_argument("--port", type=int,
    help="TCP port number to listen to.  Default is a random port.")
parser.add_argument("bunq_user_name",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
parser.add_argument("bunq_account_name",
    help="Bunq account name (retrieve using 'python3 list_user.py')")
parser.add_argument("ynab_budget_name",
    help="YNAB user name (retrieve using 'python3 list_budget.py')")
parser.add_argument("ynab_account_name",
    help="YNAB account name (retrieve using 'python3 list_budget.py')")
parser.add_argument("single_ip", action="store_true",
    help="Register BUNQ device-server for current public IP only")
args = parser.parse_args()
log_level = 2 if args.vv else 1 if args.v else 0
bunq.set_log_level(log_level)

bunq_user_id = None
serversocket = None
callback_ip = None
callback_port = None
local_port = None
portmap_port = None


# ----- Adding a callback to the bunq account

def add_callback(ip, port):
    print("Registering callback for port {}:{}...".format(ip, port))
    url = "https://{}:{}/bunq2ynab-autosync".format(ip, port)
    print("Adding BUNQ callback to: {}".format(url))
    set_autosync_callbacks([{
        "category": "MUTATION",
        "notification_target": url
    }])


def remove_callback():
    set_autosync_callbacks([])


def set_autosync_callbacks(new_nfs):
    old_nfs = bunq_api.get_callbacks(bunq_user_id, bunq_account_id)
    for nfi in old_nfs:
        for nf in nfi.values():
            if (nf["category"] == "MUTATION" and
                    nf["notification_target"].endswith("/bunq2ynab-autosync")):
                print("Removing old callback...")
            else:
                new_nfs.append({
                    "category": nf["category"],
                    "notification_target": nf["notification_target"]
                })
    bunq_api.put_callbacks(bunq_user_id, bunq_account_id, new_nfs)


# ----- Synchronize with YNAB

def sync():
    try:
        print(time.strftime('%Y-%m-%d %H:%M:%S') + " Reading list of payments...")
        transactions = bunq_api.get_payments(bunq_user_id, bunq_account_id)
        print("Uploading {} transactions to YNAB...".format(len(transactions)))
        stats = ynab.upload_payments(ynab_budget_id, ynab_account_id,
                                     transactions)
        print(time.strftime('%Y-%m-%d %H:%M:%S') + " Finished sync")
        print("")
    except Exception as e:
        print("Error during synching: {}".format(e))


# ----- Listen for bunq calls and run scheduled jobs

def bind_port():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if args.port:
        serversocket.bind(('0.0.0.0', args.port))
        return serversocket, args.port
    port = None
    for i in range(0, 128):
        port = network.next_port(port)
        try:
            serversocket.bind(('0.0.0.0', port))
            return serversocket, port
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                print("Port {0} is in use, trying next port...".format(port))
                continue
            raise
    raise Exception("No free port found")


# ----- Setup callback, wait for callback, teardown

def setup_callback():
    global bunq_user_id, bunq_account_id, ynab_budget_id, ynab_account_id
    global serversocket, callback_ip, callback_port, local_port, portmap_port

    # Don't try to map ports if we have a public IP
    callback_ip = callback_port = None
    local_ip = network.get_local_ip()
    if not network.is_private_ip(local_ip):
        callback_ip = local_ip
    else:
        print("Host has a private IP, trying upnp port mapping...")
        network.portmap_setup()
        network.portmap_search()
        portmap_ip = network.portmap_public_ip()
        callback_ip = portmap_ip

    # Set permitted IPs for bunq register-device call
    if args.single_ip:
        if callback_ip:
            bunq.set_permitted_ips([callback_ip])
        else:
            ip = network.get_public_ip()
            bunq.set_permitted_ips([ip])
    else:
        bunq.set_permitted_ips(['*'])

    if not bunq_user_id:
        print("Getting BUNQ identifiers...")
        bunq_user_id = bunq_api.get_user_id(args.bunq_user_name)
        bunq_account_id = bunq_api.get_account_id(bunq_user_id,
                                                  args.bunq_account_name)
        print("Getting YNAB identifiers...")
        ynab_budget_id = ynab.get_budget_id(args.ynab_budget_name)
        ynab_account_id = ynab.get_account_id(ynab_budget_id,
                                               args.ynab_account_name)

    if not callback_ip:
        print("No public IP found, not registering callback.")
        return

    if not serversocket:
        serversocket, local_port = bind_port()
        print("Listening on port {0}...".format(local_port))
        serversocket.listen(5)  # max incoming calls queued
 
    if not portmap_ip:
        callback_port = local_port
    else:
        portmap_port = network.portmap_add(portmap_port, local_port)
        if not portmap_port:
            print("Failed to map port, not registering callback.")
            return
        callback_port = portmap_port
    add_callback(callback_ip, callback_port)


def wait_for_callback():
    next_refresh = time.time() + refresh_callback_minutes*60
    while True:
        time_left = next_refresh - time.time()
        if time_left < 1:
            return
        try:
            print("Waiting for callback for {} minutes...".format(
                  int(time_left/60)))
            serversocket.settimeout(time_left)
            (clientsocket, address) = serversocket.accept()
            clientsocket.close()
            print("Incoming call from {}...".format(address[0]))
            if not network.is_bunq_server(address[0]):
                print("Source IP not in BUNQ range")
            else:
                sync()
        except socket.timeout as e:
            return


def teardown_callback():
    print("Cleaning up...")
    try:
        remove_callback()
    except Exception as e:
        print("Error removing callback: {}".format(e))
    try:
        network.portmap_remove(portmap_port)
    except Exception as e:
        print("Error removing upnp port mapping: {}".format(e))


# ----- Main loop
try:
    while True:
        try:
            setup_callback()

            print("Starting periodic synchronization...")
            sync()

            if callback_ip and callback_port:
                wait_for_callback()
            else:
                print("No callback, waiting for {} minutes...".format(
                    refresh_nocallback_minutes))
                time.sleep(refresh_nocallback_minutes*60)
        except Exception as e:
            print("Error: {}".format(e))
            print(e)
            print("Error occured, waiting 10 seconds.")
            time.sleep(10)
finally:
    teardown_callback()
