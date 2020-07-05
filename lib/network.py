import ipaddress
import random
import requests
import socket

# Endpoint to determine our public facing IP for device-server
public_ip_url = "http://ip.42.pl/raw"
# Bunq server address range
bunq_network = "185.40.108.0/22"


def is_bunq_server(ip):
    if ip == "172.105.76.249":
        return True
    return ipaddress.ip_address(ip) in ipaddress.ip_network(bunq_network)


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def is_private_ip(ip):
    return ipaddress.ip_address(ip).is_private


def get_public_ip():
    print("Retrieving public IP from {}...".format(public_ip_url))
    return requests.get(public_ip_url).text


upnp_init = False
upnp = None


def next_port(port):
    min_port = 49152
    max_port = 65535
    if not port:
        return random.randint(min_port, max_port)
    if port > max_port:
        return min_port
    return port + 1


def portmap_setup():
    global upnp_init, upnp
    if upnp_init:
        return
    upnp_init = True
    try:
        import miniupnpc
        upnp = miniupnpc.UPnP()
        upnp.discoverdelay = 3
    except ImportError:
        print("Could not load miniupnpc module. Skipping upnp port mapping.")


def portmap_search():
    if not upnp:
        return
    print("Searching for upnp gateway...")
    try:
        upnp.discover()
        upnp.selectigd()
    except Exception as e:
        print("Error searching for upnp gateway: {0}".format(e))


def portmap_public_ip():
    if not upnp:
        return None
    try:
        return upnp.externalipaddress()
    except:
        return None


def portmap_add(try_port, local_port):
    if not upnp:
        return
    if not try_port:
        try_port = local_port
    print("Adding upnp port mapping...")
    for i in range(0, 128):
        try:
            upnp.addportmapping(try_port, 'TCP', upnp.lanaddr, local_port,
                                'bynq2ynab-autosync', '')
            return try_port
        except Exception as e:
            if "ConflictInMappingEntry" not in str(e):
                print("Failed to map port: {}".format(e))
                return
            print("Port {} is already mapped, trying next port..."
                  .format(try_port))
            try_port = next_port(try_port)


def portmap_remove(port):
    if not upnp or not port:
        return
    print("Removing upnp port {} mapping...".format(port))
    try:
        result = upnp.deleteportmapping(port, 'TCP')
        if not result:
            print("Failed to remove upnp port mapping.")
    except Exception as e:
        print("Error removing upnp port mapping: {0}".format(e))
