from conf import *


def recv_request(conn):
    # receive the request as string
    request = conn.recv(MAX_REQ).decode('utf-8')

    # print it to the terminal
    print('\r\n\r\n')
    print(request)

    # split it
    request = request.split('\r\n')

    return request


def parse_request(conn):
    # Read the request
    req = recv_request(conn)

    # Parse the request method, path and http version
    method, path, version = req[0].split()

    # Parse the headers
    headers = {}
    data = []
    for i in range(1, len(req)):
        if req[i] == '':
            data = req[i + 1:] if i + 1 < len(req) else []
            break
        key, value = req[i].split(': ', 1)
        headers[key] = value

    return method, path, version, headers, data
