import requests


# Endpoint to determine our public facing IP for device-server
public_ip_url = "http://ip.42.pl/raw"


def get_ip():
    return requests.get(public_ip_url).text
