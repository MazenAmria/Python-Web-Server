#!/usr/bin/python

from socket import *
import os
import sys
import pandas
import re
import time
from datetime import datetime
from pytz import timezone
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


# HTTP response status codes
STATUS = {
    200: 'OK',
    404: 'Not Found'
}

# HTTP versio used by the server
VERSION = 'HTTP/1.1'

# Supported files by the server
TYPES = {
    'html': 'text/html',
    'js': 'application/javascript',
    'json': 'application/json',
    'png': 'image/png',
    'jpg': 'image/jpg',
    'ico': 'image/x-icon'
}

# Time-zone used by the server
TIMEZONE = timezone('GMT')

# Date foramt used by the server
DATEFMT = '%a, %d %b %Y %H:%M:%S %Z'


# Send HTTP response headers and data
def send_res(conn, status_code, headers, data):
    # Set the Content-Length header
    headers['Content-Length'] = len(data)

    # Set the Date header
    now = datetime.now(TIMEZONE)
    now = now.strftime(DATEFMT)
    headers['Date'] = now

    # Set the Server header
    headers['Server'] = ' '.join(os.uname())

    # Send the response status
    conn.send(
        f'{VERSION} {status_code} {STATUS[status_code]}\r\n'.encode('utf-8'))

    # Send the headers
    for (key, value) in headers.items():
        conn.send(f'{key}: {value}\r\n'.encode('utf-8'))

    # End of headers section
    conn.send(b'\r\n')

    # Send the payload
    conn.send(data)


def smartphones_handler(conn, addr, method, path, version, req_headers):
    """A handler for '/SortName' and '/SortPrice'
    """
    try:
        smartphones = pandas.read_csv('smartphones.csv')

        # Sort depending on the desired column
        col = path[len("/Sort"):]
        res = smartphones.sort_values(col)

        # Set Headers
        status_code = 200
        mod = datetime.fromtimestamp(
            os.path.getmtime('smartphones.csv'), TIMEZONE)
        mod = mod.strftime(DATEFMT)
        res_headers = {
            'Content-Type': 'application/json',
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        # Set Data
        data = res.to_json(orient='records').encode('utf-8')

        # Send the response
        send_res(conn, status_code, res_headers, data)
        return True
    except Exception as e:
        logging.error("%s: %s", sys._getframe().f_code.co_name, e)
        return False


def absolute_handler(conn, addr, method, path, version, req_headers):
    """A handler for '/' returns index.html.
    """
    try:
        file = open('index.html', 'rb')

        # Set the Headers
        status_code = 200
        mod = datetime.fromtimestamp(os.path.getmtime(path), TIMEZONE)
        mod = mod.strftime(DATEFMT)
        res_headers = {
            'Content-Type': 'text/html',
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        # Set the Data
        data = file.read()

        # Send the response
        send_res(conn, status_code, res_headers, data)
        return True
    except Exception as e:
        logging.error("%s: %s", sys._getframe().f_code.co_name, e)
        return False


def default_handler(conn, addr, method, path, version, req_headers):
    """A default handler that returns a file 
    if it exists and return 404 page otherwise.
    """
    # remove the starting '/'
    path = path[1:]

    extension = path.split('.')[-1]

    try:
        file = open(path, 'rb')

        # Set the Headers
        status_code = 200
        mod = datetime.fromtimestamp(os.path.getmtime(path), TIMEZONE)
        mod = mod.strftime(DATEFMT)
        res_headers = {
            'Content-Type': TYPES[extension],
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        # Set the Data
        data = file.read()

        # Send the response
        send_res(conn, status_code, res_headers, data)
    except Exception as e:
        logging.error("%s: %s", sys._getframe().f_code.co_name, e)
        # Requested Object Not Found
        file = open('notfound.html', 'r')

        # Set Headers
        status_code = 404
        mod = datetime.now(TIMEZONE)
        mod = mod.strftime(DATEFMT)
        res_headers = {
            'Content-Type': 'text/html',
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        # Set the Data
        data = file.read()

        # Render the addresses
        data = data.replace('{{ client-ip }}', str(addr[0]))
        data = data.replace('{{ client-port }}', str(addr[1]))
        data = data.replace('{{ server-ip }}', str(conn.getsockname()[0]))
        data = data.replace('{{ server-port }}', str(conn.getsockname()[1]))

        # Encode Data
        data.encode('utf-8')

        # Send the response
        send_res(conn, status_code, res_headers, data)
    finally:
        return True


# define list of handlers
handlers = [
    (re.compile(r'^/$'), absolute_handler),
    (re.compile(r'^/Sort'), smartphones_handler),
    (re.compile(r''), default_handler)
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
        if req[i] == '':
            break
        key, value = req[i].split(': ', 1)
        headers[key] = value

    logging.info('%s %s from %s', method, path, client_address)

    handled = False
    for handler in handlers:
        # If the Request matches the handler
        if handler[0].match(path):
            # Try to handle it
            handled = handler[1](client_socket, client_address,
                                 method, path, version, headers)
            # If it has been handled stop, otherwise try other handlers
            if handled:
                break

    # Close the connection
    client_socket.close()
