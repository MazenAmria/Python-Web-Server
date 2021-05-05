import sys

import pandas

from response import *

FORMAT = '%(asctime)-15s\t[%(levelname)s]: * %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def _smartphones_handler(conn, addr, req_path, req_version, req_headers, req_data):
    """A handler for '/SortName' and '/SortPrice'
    """
    try:
        smartphones = pandas.read_csv('smartphones.csv')

        # Sort depending on the desired column
        col = req_path[len("/Sort"):]
        res = smartphones.sort_values(col)

        # Set Headers
        status_code = 200
        mod = datetime.fromtimestamp(
            os.path.getmtime('smartphones.csv'), TIMEZONE)
        mod = mod.strftime(DATE_FMT)
        res_headers = {
            'Content-Type': 'application/json',
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        # Set Data
        res_data = res.to_json(orient='records').encode('utf-8')

        # Send the response
        send_res(conn, status_code, res_headers, res_data)
        return True
    except Exception as e:
        logging.error("%s: %s", sys._getframe().f_code.co_name, e)
        return False


def _root_handler(conn, addr, req_path, req_version, req_headers, req_data):
    """A handler for '/' returns index.html.
    """
    try:
        file = open('index.html', 'rb')

        # Set the Headers
        status_code = 200
        mod = datetime.fromtimestamp(os.path.getmtime(req_path), TIMEZONE)
        mod = mod.strftime(DATE_FMT)
        res_headers = {
            'Content-Type': 'text/html',
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        # Set the Data
        res_data = file.read()

        # Send the response
        send_res(conn, status_code, res_headers, res_data)
        return True
    except Exception as e:
        logging.error("%s: %s", sys._getframe().f_code.co_name, e)
        return False


def _default_handler(conn, addr, req_path, req_version, req_headers, req_data):
    """A default handler that returns a file
    if it exists and return 404 page otherwise.
    """
    try:
        # remove the starting '/'
        req_path = req_path[1:]
        file = open(req_path, 'rb')

        # Set the Headers
        status_code = 200
        mod = datetime.fromtimestamp(os.path.getmtime(req_path), TIMEZONE)
        mod = mod.strftime(DATE_FMT)
        res_headers = {
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        for tp in TYPES:
            if tp[0].match(req_path):
                res_headers['Content-Type'] = tp[1]
                break

        # Set the Data
        res_data = file.read()

        # Send the response
        send_res(conn, status_code, res_headers, res_data)
    except Exception as e:
        logging.error("%s: %s", sys._getframe().f_code.co_name, e)
        # Requested Object Not Found
        file = open('notfound.html', 'r')

        # Set Headers
        status_code = 404
        mod = datetime.now(TIMEZONE)
        mod = mod.strftime(DATE_FMT)
        res_headers = {
            'Content-Type': 'text/html',
            'Last-Modified': mod,
            'Connection': req_headers['Connection']
        }

        # Set the Data
        res_data = file.read()

        # Render the addresses
        res_data = res_data.replace('{{ client-ip }}', str(addr[0]))
        res_data = res_data.replace('{{ client-port }}', str(addr[1]))
        res_data = res_data.replace('{{ server-ip }}', str(conn.getsockname()[0]))
        res_data = res_data.replace('{{ server-port }}', str(conn.getsockname()[1]))

        # Encode Data
        res_data = res_data.encode('utf-8')

        # Send the response
        send_res(conn, status_code, res_headers, res_data)
    finally:
        return True


# define list of handlers
HANDLERS = [
    (re.compile(r'^/$'), 'GET', _root_handler),
    (re.compile(r'^/Sort'), 'GET', _smartphones_handler),
    (re.compile(r''), 'GET', _default_handler)
]
