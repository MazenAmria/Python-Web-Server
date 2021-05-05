#!/usr/bin/python

from socket import *

from handlers import *
from request import *
from response import *

FORMAT = '%(asctime)-15s\t[%(levelname)s]: * %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

# IPv4
server_socket = socket(AF_INET, SOCK_STREAM)

# Allow socket reuse
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Bind the address to the socket
server_socket.bind((SRV_HOST, SRV_PORT))

# Listening with maximum connections = Q_SIZE
server_socket.listen(Q_SIZE)

logging.info("Starts Listening at http://%s:%s/", SRV_HOST, SRV_PORT)

while True:
    # Accept a request
    client_socket, client_address = server_socket.accept()

    # Parse the request
    method, path, version, headers, data = parse_request(client_socket)

    logging.info('%s %s from %s', method, path, client_address)

    # Try the handlers
    for handler in HANDLERS:
        if handler[0].match(path) and handler[1] == method:
            # Try to handle it
            if handler[2](client_socket, client_address, path, version, headers, data):
                break

    # Close the connection
    client_socket.close()
