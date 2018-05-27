import ipaddress
import requests
import socket


# Endpoint to determine our public facing IP for device-server
public_ip_url = "http://ip.42.pl/raw"


def get_public_ip():
    return requests.get(public_ip_url).text


def addressInNetwork(ip, net_n_bits):
    return ipaddress.ip_address(ip) in ipaddress.ip_network(net_n_bits)


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


upnp = None
mapped_port = None

def open_port(port):
    try:
        import miniupnpc
    except ImportError:
        print("Could not load miniupnpc module. Skipping upnp forward.")
        return
    global upnp
    print("Searching for upnp gateway...")
    try:
        upnp = miniupnpc.UPnP()
        upnp.selectigd()
    except Exception as e:
        print(e)
        return
    print("Adding port forwarding...")
    try:
        result = upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'bynq2ynab-autosync', '')
        if not result:
            print("Could not add port forwarding.")
            return
    except Exception as e:
        print(e)
        return
    global mapped_port
    mapped_port = port


def close_port():
    if not mapped_port:
        return
    print("Removing port forwarding...")
    try:
        result = upnp.deleteportmapping(mapped_port, 'TCP')
        if not result:
            print("Failed to remove upnp port forwarding.")
    except Exception as e:
        print(e)
