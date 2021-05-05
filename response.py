import logging
from datetime import datetime

from conf import *

FORMAT = '%(asctime)-15s\t[%(levelname)s]: * %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def send_res(conn, status_code, res_headers, res_data):
    # Set the Content-Length header
    res_headers['Content-Length'] = len(res_data)

    # Set the Date header
    now = datetime.now(TIMEZONE)
    now = now.strftime(DATE_FMT)
    res_headers['Date'] = now

    # Set the Server header
    res_headers['Server'] = SERVER

    # Send the response status
    conn.send(
        f'{VERSION} {status_code} {STATUS[status_code]}\r\n'.encode('utf-8'))

    logging.info('%s %s %s', VERSION, status_code, STATUS[status_code])
    # Send the headers
    for (key, value) in res_headers.items():
        conn.send(f'{key}: {value}\r\n'.encode('utf-8'))

    # End of headers section
    conn.send(b'\r\n')

    # Send the payload
    conn.send(res_data)
