#!/usr/bin/python

from socket import *
import pandas
import re
import time
import logging

FORMAT = '%(asctime)-15s\t[%(levelname)s]: * %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def recv_request(csock):
    # recieve the request as string
    req = csock.recv(8192).decode('utf-8')

    # print it to the terminal
    print(req)

    # parse it
    req = req.split('\r\n')

    return req


def smartphones_handler(conn, addr, method, path, version, headers):
    """A handler for '/SortName' and '/SortPrice'
    """
    try:
        smartphones = pandas.read_csv('smartphones.csv')
        col = path[len("/Sort"):]
        res = smartphones.sort_values(col)
        conn.send(f'{version} 200 OK\r\n'.encode('utf-8'))
        conn.send(b'Content-Type: application/json\r\n')
        conn.send(b'\r\n')
        conn.send(res.to_json(orient='records').encode('utf-8'))
        return True
    except Exception as e:
        logging.error("%s: %s", __name__, e)
        return False


def absolute_handler(conn, addr, method, path, version, headers):
    """A handler for '/' returns index.html.
    """
    try:
        file = open('index.html', 'rb')
        conn.send(f'{version} 200 OK\r\n'.encode('utf-8'))
        conn.send(b'Content-Type: text/html\r\n')
        conn.send(b'\r\n')
        res = file.read()
        conn.send(res)
        return True
    except Exception as e:
        logging.error("%s: %s", __name__, e)
        return False


def default_handler(conn, addr, method, path, version, headers):
    """A default handler that returns a file 
    if it exists and return 404 page otherwise.
    """
    # remove the starting '/'
    path = path[1:]

    # determine the type
    types = {
        'html': 'text/html',
        'js': 'application/javascript',
        'json': 'application/json',
        'png': 'image/png',
        'jpg': 'image/jpg'
    }
    extension = path.split('.')[-1]
    # try to open the file
    try:
        file = open(path, 'rb')
        conn.send(f'{version} 200 OK\r\n'.encode('utf-8'))
        conn.send(f'Content-Type: {types[extension]}\r\n'.encode('utf-8'))
        conn.send(b'\r\n')
        res = file.read()
        conn.send(res)
    except:
        file = open('notfound.html', 'r')
        conn.send(f'{version} 404 OK\r\n'.encode('utf-8'))
        conn.send(b'Content-Type: text/html\r\n')
        conn.send(b'\r\n')
        res = file.read()
        # Render the addresses
        res = res.replace('{{ client-ip }}', str(addr[0]))
        res = res.replace('{{ client-port }}', str(addr[1]))
        res = res.replace('{{ server-ip }}', str(conn.getsockname()[0]))
        res = res.replace('{{ server-port }}', str(conn.getsockname()[1]))

        conn.send(res.encode('utf-8'))


# define list of handlers
handlers = [
    (re.compile(r'^/$'), absolute_handler),
    (re.compile(r'^/Sort'), smartphones_handler)
]

# IPv4
server_socket = socket(AF_INET, SOCK_STREAM)

# Accept requests on all interfaces ar port 9000
SRVHOST = "0.0.0.0"
SRVPORT = 9000

# Allow socket reuse
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Bind the address to the socket
server_socket.bind((SRVHOST, SRVPORT))

# Listening with maximum connections = 10
QSIZ = 10
server_socket.listen(QSIZ)

logging.info("Starts Listening at http://%s:%s/", SRVHOST, SRVPORT)

while True:
    client_socket, client_address = server_socket.accept()

    # Read the request
    req = recv_request(client_socket)

    # Extract the method, path and HTTP version of the request
    method, path, version = req[0].split()

    # Extract the headers
    headers = {}
    for i in range(1, len(req)):
        if req[i] == "":
            break
        key, value = req[i].split(': ', 1)
        headers[key] = value

    logging.info('%s %s from %s', method, path, client_address)

    handled = False
    for handler in handlers:
        if handler[0].match(path):
            handled = handler[1](client_socket, client_address,
                                 method, path, version, headers)
            if handled:
                break

    if not handled:
        default_handler(client_socket, client_address,
                        method, path, version, headers)

    # Close the connection
    client_socket.close()
