import ipaddress
import requests
import socket


# Endpoint to determine our public facing IP for device-server
public_ip_url = "http://ip.42.pl/raw"
# Bunq server address range
bunq_network = "185.40.108.0/22"


# Can't change public IP, it's also saved in the IP limits on the API key
public_ip = None


def get_public_ip():
    global public_ip
    if not public_ip:
        public_ip = requests.get(public_ip_url).text
    return public_ip


def is_bunq_server(ip):
    return ipaddress.ip_address(ip) in ipaddress.ip_network(bunq_network)


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


upnp = None
local_port = None
public_port = None


def portmap_setup(port):
    # Don't try to map ports if we have a public IP
    if get_public_ip() == get_local_ip():
        print("Host has a public IP, not trying upnp port mapping.")
        return
    global upnp, local_port
    local_port = port
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


def portmap_add():
    if not upnp:
        return
    print("Adding upnp port mapping...")
    global public_port
    for try_port in range(local_port, local_port+128):
        try:
            upnp.addportmapping(try_port, 'TCP', upnp.lanaddr, local_port,
                                'bynq2ynab-autosync', '')
            public_port = try_port
            return public_port
        except Exception as e:
            if "ConflictInMappingEntry" not in str(e):
                raise e
            print("Port {} is already mapped, trying next port..."
                  .format(try_port))


def portmap_remove():
    global public_port
    if not upnp or not public_port:
        return
    print("Removing upnp port mapping...")
    try:
        result = upnp.deleteportmapping(public_port, 'TCP')
        if not result:
            print("Failed to remove upnp port mapping.")
    except Exception as e:
        print("Error removing upnp port mapping: {0}".format(e))
    finally:
        public_port = None
