import errno
import random
import socket
import time
import traceback

from lib import bunq_api
from lib import network
from lib import sync
from lib import helpers
from lib.config import config
from lib.log import log


# ----- Parse command line arguments

config.parser.add_argument("--port", type=int,
    help="TCP port number to listen to.  Default is a random port")
config.parser.add_argument("--external-port", type=int,
    help="TCP port number to register for callback")
# Don't set defaults here.  A default looks like a command line parameter,
# so lib.config would ignore an entry in config.json
config.parser.add_argument("--wait", type=int,
    help="Synch time when there is no callback.  Default 60 minutes (1 hour)")
config.parser.add_argument("--interval", type=int,
    help="Synch time with callback.  Defaults 240 minutes (4 hours)")
config.parser.add_argument("--refresh", type=int,
    help="Time to refresh callback setup.  Defaults 480 minutes (8 hours)")
config.parser.add_argument("--callback-marker",
    help="Unique marker for callbacks.  Defaults bunq2ynab-autosync")
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
        port = random.randint(1025, 65535)
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
        log.info("Host has a private IP.  A port is specified so we will not "
                 "attempt to map a port.  Remember to configure forward "
                 "manually.")
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

    marker = config.get("callback_marker") or "bunq2ynab-autosync"
    external_port = config.get("external_port")
    if not using_portmap:
        callback_port = external_port or local_port
    elif external_port:
        log.info(f"Forwarding specified port {external_port}...")
        network.portmap_add(external_port, local_port, marker)
        callback_port = external_port  # Regardless of success
    else:
        log.info("Looking for port to forward...")
        portmap_port = network.portmap_seek(local_port, marker)
        if not portmap_port:
            log.error("Failed to map port, not registering callback.")
            return
        log.info(f"Succesfully forwarded port {portmap_port}")
        callback_port = portmap_port

    if callback_port != 443:
        log.warning(f"Callbacks port is {callback_port}.  Callbacks are "
                    f"broken for ports other than 443")
    for uid in sync_obj.get_bunq_user_ids():
        url = "https://{}:{}/{}".format(callback_ip, callback_port, marker)
        bunq_api.add_callback(uid, marker, url)


def wait_for_callback():
    refresh = (config.get("refresh") or 8*60)*60
    interval = (config.get("interval") or 4*60)*60
    last_sync = time.time()
    next_refresh = time.time() + refresh
    next_sync = time.time() + interval
    while True:
        time_left = max(min(next_sync, next_refresh) - time.time(), 0)
        log.info("Waiting for callback for {}...".format(
              helpers.format_seconds(time_left)))
        serversocket.settimeout(time_left)
        try:
            (clientsocket, address) = serversocket.accept()
            clientsocket.close()
            source_ip = address[0]
            log.info("Incoming call from {}...".format(source_ip))
            if not network.is_bunq_server(source_ip):
                log.warning(f"Source {source_ip} not in BUNQ range")
                continue
        except socket.timeout as e:
            pass

        if next_refresh <= time.time():
            return
        if time.time() < last_sync + 30:
            next_sync = last_sync + 30
        else:
            log.info("Synchronizing periodically...")
            synchronize()
            last_sync = time.time()
            next_sync = last_sync + interval


def teardown_callback():
    log.info("Cleaning up...")
    callback_marker = config.get("callback_marker") or "bunq2ynab-autosync"
    for uid in sync_obj.get_bunq_user_ids():
        try:
            bunq_api.remove_callback(uid, callback_marker)
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
    wait = (config.get("wait") or 1) * 60
    next_sync = 0
    while True:
        try:
            sync_obj = sync.Sync()
            sync_obj.populate()

            if next_sync < time.time():
                log.info("Synchronizing at start or before refresh...")
                synchronize()
                next_sync = time.time() + wait

            setup_callback()
            if callback_ip and callback_port:
                wait_for_callback()
            else:
                time_left = max(next_sync - time.time(), 0)
                log.warning("No callback, waiting for .{} minutes...".format(
                    int(time_left/60)))
                time.sleep(time_left)

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
