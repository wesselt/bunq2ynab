import argparse
import socket
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("--port", default=443, type=int,
    help="TCP port number to listen to")
args = parser.parse_args()


serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('0.0.0.0', args.port))
serversocket.listen(5)

print("Listening on port {0}".format(args.port))
while True:
    (clientsocket, address) = serversocket.accept()
    print("Incoming call from {0}...".format(address[0]))
    clientsocket.close()
