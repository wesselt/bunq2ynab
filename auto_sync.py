import errno
import socket
import time
import traceback

from lib import bunq_api
from lib import network
from lib import sync
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

    for acc in sync_obj.get_bunq_accounts():
        url = "https://{}:{}/bunq2ynab-autosync".format(
                                                    callback_ip, callback_port)
        bunq_api.add_callback(acc["bunq_user_id"], acc["bunq_account_id"],
            "bunq2ynab-autosync", url)


def wait_for_callback():
    last_sync = time.time()
    next_refresh = time.time() + refresh_callback_minutes*60
    next_sync = next_refresh
    while True:
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

        if next_refresh <= time.time():
            return
        elif time.time() < last_sync + 30:
            next_sync = last_sync + 30
        else:
            synchronize()
            last_sync = time.time()
            next_sync = next_refresh


def teardown_callback():
    log.info("Cleaning up...")
    for acc in sync_obj.get_bunq_accounts():
        try:
            bunq_api.remove_callback(acc["bunq_user_id"], 
                acc["bunq_account_id"], "bunq2ynab-autosync")
        except Exception as e:
            log.info("Error removing callback: {}".format(e))
    try:
        network.portmap_remove(portmap_port)
    except Exception as e:
        log.error("Error removing upnp port mapping: {}".format(e))


def on_error_wait_secs(consecutive_errors):
    if consecutive_errors < 60:
        return 10
    if consecutive_errors < 120:
        return 60
    return 60*60


# ----- Main loop
try:
    consecutive_errors = 0
    while True:
        try:
            sync_obj = sync.Sync()
            sync_obj.populate()

            setup_callback()

            log.info("Starting periodic synchronization...")
            synchronize()

            if callback_ip and callback_port:
                wait_for_callback()
            else:
                log.warning("No callback, waiting for {} minutes...".format(
                    refresh_nocallback_minutes))
                time.sleep(refresh_nocallback_minutes*60)

            consecutive_errors = 0
        except Exception as e:
            log.error("Error: {}".format(e))
            log.error(traceback.format_exc())
            consecutive_errors += 1
            wait_secs = on_error_wait_secs(consecutive_errors)
            log.error(f"Failed {consecutive_errors} times, " +
                f"waiting {wait_secs} seconds for retry.")
            time.sleep(wait_secs)
finally:
    teardown_callback()
