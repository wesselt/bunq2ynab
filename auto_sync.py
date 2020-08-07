import errno
import socket
import time
import traceback

from lib import bunq
from lib import bunq_api
from lib import network
from lib import sync
from lib import ynab
from lib import helpers
from lib.config import config
from lib.log import log


# ----- Parameters

refresh_callback_minutes = 8*60
refresh_nocallback_minutes = 60 


# ----- Parse command line arguments

config.parser.add_argument("--port", type=int,
    help="TCP port number to listen to.  Default is a random port.")
config.load()


serversocket = None
callback_ip = None
callback_port = None
local_port = None
portmap_port = None
sync_obj = None


# ----- Adding a callback to the bunq account

def add_callback(bunq_user_id, bunq_account_id, ip, port):
    log.info("Registering callback for port {}:{}...".format(ip, port))
    url = "https://{}:{}/bunq2ynab-autosync".format(ip, port)
    log.info("Adding BUNQ callback to: {}".format(url))
    set_autosync_callbacks(bunq_user_id, bunq_account_id, [{
        "category": "MUTATION",
        "notification_target": url
    }])


def remove_callback(bunq_user_id, bunq_account_id):
    set_autosync_callbacks(bunq_user_id, bunq_account_id, [])


def set_autosync_callbacks(bunq_user_id, bunq_account_id, new_nfs):
    if not bunq_user_id or not bunq_user_id:
        log.info("Can't change callbacks without user and account id.")
        return

    old_nfs = bunq_api.get_callbacks(bunq_user_id, bunq_account_id)
    for nfi in old_nfs:
        for nf in nfi.values():
            if (nf["category"] == "MUTATION" and
                    nf["notification_target"].endswith("/bunq2ynab-autosync")):
                log.info("Removing callback...")
            else:
                new_nfs.append({
                    "category": nf["category"],
                    "notification_target": nf["notification_target"]
                })
    bunq_api.put_callbacks(bunq_user_id, bunq_account_id, new_nfs)


# ----- Synchronize with YNAB

def synchronize():
    try:
        log.info("Starting sync at " + time.strftime('%Y-%m-%d %H:%M:%S'))
        sync_obj.synchronize()
        log.info("Finished sync at " + time.strftime('%Y-%m-%d %H:%M:%S'))
        log.info("")
    except Exception as e:
        log.error("Error during synching: {}".format(e))
        log.error(traceback.format_exc())


# ----- Listen for bunq calls and run scheduled jobs

def bind_port():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = config.get("port")
    if port:
        serversocket.bind(('0.0.0.0', int(port)))
        return serversocket, int(port)
    port = None
    for i in range(0, 128):
        port = network.next_port(port)
        try:
            serversocket.bind(('0.0.0.0', port))
            return serversocket, port
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                log.warning("Port {0} is in use, trying next...".format(port))
                continue
            raise
    raise Exception("No free port found")


# ----- Setup callback, wait for callback, teardown

def setup_callback():
    global serversocket, callback_ip, callback_port, local_port, portmap_port

    # Don't try to map ports if we have a public IP
    callback_ip = callback_port = None
    using_portmap = False
    local_ip = network.get_local_ip()
    if not network.is_private_ip(local_ip):
        log.info("Host has a public IP...")
        callback_ip = local_ip
    elif config.get("port"):
        log.info("Host has a private IP, port specified, configure forward " +
                 "manually...")
        callback_ip = network.get_public_ip()
    else:
        log.info("Host has a private IP, trying upnp port mapping...")
        network.portmap_setup()
        network.portmap_search()
        callback_ip = network.get_public_ip()
        using_portmap = True

    if not callback_ip:
        log.error("No public IP found, not registering callback.")
        return

    if not serversocket:
        serversocket, local_port = bind_port()
        log.info("Listening on port {0}...".format(local_port))
        serversocket.listen(5)  # max incoming calls queued
 
    if not using_portmap:
        callback_port = local_port
    else:
        portmap_port = network.portmap_add(portmap_port, local_port)
        if not portmap_port:
            log.error("Failed to map port, not registering callback.")
            return
        callback_port = portmap_port

    sync_obj.populate()
    for acc in sync_obj.get_bunq_accounts():
        add_callback(acc["bunq_user_id"], acc["bunq_account_id"],
                     callback_ip, callback_port)


def wait_for_callback():
    last_sync = time.time()
    next_refresh = time.time() + refresh_callback_minutes*60
    next_sync = next_refresh
    while time.time() < next_refresh:
        time_left = max(min(next_sync, next_refresh) - time.time(), 0)
        log.info("Waiting for callback for {}...".format(
              helpers.format_seconds(time_left)))
        serversocket.settimeout(time_left)
        try:
            (clientsocket, address) = serversocket.accept()
            clientsocket.close()
            if not network.is_bunq_server(address[0]):
                log.warning("Source IP not in BUNQ range".format(address[0]))
                continue
            log.info("Incoming call from {}...".format(address[0]))
        except socket.timeout as e:
            pass

        if time.time() < last_sync + 30:
            next_sync = last_sync + 30
        else:
            synchronize()
            last_sync = time.time()
            next_sync = next_refresh


def teardown_callback():
    log.info("Cleaning up...")
    for acc in sync_obj.get_bunq_accounts():
        try:
            remove_callback(acc["bunq_user_id"], acc["bunq_account_id"])
        except Exception as e:
            log.info("Error removing callback: {}".format(e))
    try:
        network.portmap_remove(portmap_port)
    except Exception as e:
        log.error("Error removing upnp port mapping: {}".format(e))


# ----- Main loop
try:
    while True:
        try:
            sync_obj = sync.Sync()

            setup_callback()

            log.info("Starting periodic synchronization...")
            synchronize()

            if callback_ip and callback_port:
                wait_for_callback()
            else:
                log.warning("No callback, waiting for {} minutes...".format(
                    refresh_nocallback_minutes))
                time.sleep(refresh_nocallback_minutes*60)
        except Exception as e:
            log.error("Error: {}".format(e))
            log.error(traceback.format_exc())
            log.error("Error occured, waiting 10 seconds.")
            time.sleep(10)
finally:
    teardown_callback()
