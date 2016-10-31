import sys
import re
import csv
import httplib
from datetime import datetime
from HTMLParser import HTMLParser

html = HTMLParser()


# Some predefined variables


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

csv_headers = {
    'source': 'Source',
    'id': 'Source ID',
    'category': 'Category',
    'category_id': 'Category ID',
    'name': 'Name',
    'palette': 'Palette',
    'threadcount': 'Threadcount',
    'overview': 'Overview',
    'comment': 'Comment',
    'copyright': 'Copyright',
    'url': 'Source URL',
    'updated': 'Update date'
}

csv_column_order = [
    'source', 'id', 'category', 'category_id', 'name',
    'palette', 'threadcount', 'overview', 'comment', 'copyright',
    'url', 'updated'
]


# Utilities


def new_tartan():
    result = {}
    for key in csv_headers:
        result[key] = ''
    result['updated'] = now()
    return result


def now():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def cleanup_str(value):
    value = html.unescape(value)
    value = re.sub('\s+', ' ', value, flags=re.IGNORECASE)
    value = value.strip()
    return value


def get_connection(host):
    return httplib.HTTPConnection(host)

# Logging


def log_message(message):
    sys.stderr.write(message)


def log_source(source):
    sys.stderr.write(Colors.HEADER + source + Colors.ENDC + '\n')


def log_started():
    sys.stderr.write(Colors.OKBLUE + 'Started...' + Colors.ENDC + '\n')


def log_finished():
    sys.stderr.write(Colors.OKBLUE + 'Finished.' + Colors.ENDC + '\n')


def log_http_status(code, reason, prefix='', suffix=''):
    color = {
        1: Colors.WARNING,
        2: Colors.OKGREEN,
        3: Colors.WARNING,
        4: Colors.FAIL,
        5: Colors.FAIL
    }[int(code / 100)]
    message = \
        color + prefix + str(code) + ' ' + str(reason) + \
        suffix + Colors.ENDC
    sys.stderr.write(message)


def log_url(url, prefix='', suffix=''):
    url = Colors.UNDERLINE + url + Colors.ENDC
    sys.stderr.write(prefix + url + suffix)


# Printing


def print_bom():
    sys.stdout.write('\xEF\xBB\xBF')


def print_csv_headers(bom=True):
    if bom:
        print_bom()
    print_csv_row(csv_headers)


def print_csv_row(row):
    data = []
    for c in csv_column_order:
        data.append(unicode(row[c]).encode('utf-8'))
    writer = csv.writer(
        sys.stdout,
        delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL,
        escapechar='\\', doublequote=True
    )
    writer.writerow(data)
