import os
import re
from pytz import timezone

# Server Interfaces and Port
SRV_HOST = "0.0.0.0"
SRV_PORT = 9000

# Maximum requests in the queue
Q_SIZE = 10

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

# Date format used by the server
DATE_FMT = '%a, %d %b %Y %H:%M:%S %Z'

# Information about the Server Machine
SERVER = ' '.join(os.uname())
