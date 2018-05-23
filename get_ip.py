import requests
import socket
import struct


# Endpoint to determine our public facing IP for device-server
public_ip_url = "http://ip.42.pl/raw"


def get_ip():
    return requests.get(public_ip_url).text

# https://stackoverflow.com/a/819420/50552
def addressInNetwork(ip, net):
   "Is an address in a network"
   ipaddr = struct.unpack('<L', socket.inet_aton(ip))[0]
   netaddr,bits = net.split('/')
   netmask = (struct.unpack('<L', socket.inet_aton(netaddr))[0] & 
              ((2 << int(bits)-1) - 1))
   return ipaddr & netmask == netmask
