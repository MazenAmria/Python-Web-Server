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

# Server Interfaces and Port
SRVHOST = "0.0.0.0"
SRVPORT = 9000

# Maximum requests in the queue
QSIZ = 10

# Maximum request length
MAX_REQ = 8192

# HTTP response status codes
STATUS = {
    200: 'OK',
    404: 'Not Found'
}

# HTTP version used by the server
VERSION = 'HTTP/1.1'

# Supported files by the server
TYPES = [
    (re.compile(r''), 'text/plain'),
    (re.compile(r'.html$'), 'text/html'),
    (re.compile(r'.js$'), 'application/javascript'),
    (re.compile(r'.json$'), 'application/json'),
    (re.compile(r'.png$'), 'image/png'),
    (re.compile(r'.jpg$'), 'image/jpg'),
    (re.compile(r'.ico$'), 'image/x-icon'),
    (re.compile(r'.csv$'), 'text/csv')
]

# Time-zone used by the server
TIMEZONE = timezone('GMT')

# Date foramt used by the server
DATEFMT = '%a, %d %b %Y %H:%M:%S %Z'

# Information about the Server Machine
SERVER = ' '.join(os.uname())


def recv_request(conn):
    # recieve the request as string
    req = conn.recv(MAX_REQ).decode('utf-8')

    # print it to the terminal
    print('\r\n\r\n')
    print(req)

    # split it
    req = req.split('\r\n')

    return req


def parse_headers(req):
    method, path, version = req[0].split()

    headers = {}
    for i in range(1, len(req)):
        if req[i] == '':
            break
        key, value = req[i].split(': ', 1)
        headers[key] = value

    return method, path, version, headers


# Send HTTP response headers and data
def send_res(conn, status_code, headers, data):
    # Set the Content-Length header
    headers['Content-Length'] = len(data)

    # Set the Date header
    now = datetime.now(TIMEZONE)
    now = now.strftime(DATEFMT)
    headers['Date'] = now

    # Set the Server header
    headers['Server'] = SERVER

    # Send the response status
    conn.send(
        f'{VERSION} {status_code} {STATUS[status_code]}\r\n'.encode('utf-8'))

    logging.info('%s %s %s', VERSION, status_code, STATUS[status_code])
    # Send the headers
    for (key, value) in headers.items():
        conn.send(f'{key}: {value}\r\n'.encode('utf-8'))

    # End of headers section
    conn.send(b'\r\n')

    # Send the payload
    conn.send(data)


def smartphones_handler(conn, addr, path, version, req_headers):
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


def root_handler(conn, addr, path, version, req_headers):
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


def default_handler(conn, addr, path, version, req_headers):
    """A default handler that returns a file 
    if it exists and return 404 page otherwise.
    """
    try:
        # remove the starting '/'
        path = path[1:]
        file = open(path, 'rb')

        # Set the Headers
        status_code = 200
        mod = datetime.fromtimestamp(os.path.getmtime(path), TIMEZONE)
        mod = mod.strftime(DATEFMT)
        res_headers = {
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        for tp in TYPES:
            if tp[0].match(path):
                res_headers['Content-Type'] = tp[1]
                break

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
        data = data.encode('utf-8')

        # Send the response
        send_res(conn, status_code, res_headers, data)
    finally:
        return True


# define list of handlers
HANDLERS = [
    (re.compile(r'^/$'), 'GET', root_handler),
    (re.compile(r'^/Sort'), 'GET', smartphones_handler),
    (re.compile(r''), 'GET', default_handler)
]

# IPv4
server_socket = socket(AF_INET, SOCK_STREAM)

# Allow socket reuse
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Bind the address to the socket
server_socket.bind((SRVHOST, SRVPORT))

# Listening with maximum connections = QSIZ
server_socket.listen(QSIZ)

logging.info("Starts Listening at http://%s:%s/", SRVHOST, SRVPORT)

while True:
    client_socket, client_address = server_socket.accept()

    # Read the request
    req = recv_request(client_socket)

    # Extract the method, path, HTTP version and Request Heders
    method, path, version, headers = parse_headers(req)

    logging.info('%s %s from %s', method, path, client_address)

    for handler in HANDLERS:
        if handler[0].match(path) and handler[1] == method:
            # Try to handle it
            if handler[2](client_socket, client_address, path, version, headers):
                break

    # Close the connection
    client_socket.close()
