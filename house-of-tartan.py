import sys
import datetime
import httplib
import re
import json
import csv
from HTMLParser import HTMLParser
html = HTMLParser()

# Predefined things
host = 'www.house-of-tartan.scotland.net'

bom = '\xEF\xBB\xBF'

re_extract_ids = re.compile(
    'onclick="Frm\(\'([0-9]+)\'\)"',
    re.IGNORECASE
)

re_extract_attr = re.compile(
    '<div class="(title|ftr-hdr|ftr-txt|ftr-cpy)">(.*)</div>',
    re.IGNORECASE)

re_extract_pattern = re.compile(
    'Tartan\.setup\((".*")\);',
    re.IGNORECASE | re.DOTALL)

re_extract_category = re.compile(
    '\s+([a-z][-/a-z0-9]+)(\s+Weavers)?\s+Tartan$',
    re.IGNORECASE | re.DOTALL)

re_normalize_palette = re.compile(
    '([a-z]+)=([0-9a-f]{6})([a-z\s()]*)[;,]',
    re.IGNORECASE | re.DOTALL
)

re_normalize_threadcount = re.compile(
    '^([a-z]+)([0-9]+([a-z]+[0-9]+)+[a-z]+)([0-9]+)$',
    re.IGNORECASE
)

attr_map = {
    'title': 'name',
    'ftr-hdr': 'overview',
    'ftr-txt': 'comment',
    'ftr-cpy': 'copyright',
}

csv_headers = {
    'source': 'Source',
    'id': 'Source ID',
    'category': 'Category',
    'name': 'Name',
    'palette': 'Palette',
    'threadcount': 'Threadcount',
    'overview': 'Overview',
    'comment': 'Comment',
    'copyright': 'Copyright',
    'updated': 'Update date'
}

csv_column_order = [
    'source', 'id', 'category', 'name', 'palette', 'threadcount',
    'overview', 'comment', 'copyright', 'updated'
]


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def now():
    return datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def cleanup_str(value):
    value = html.unescape(value)
    value = re.sub('\s+', ' ', value, flags=re.IGNORECASE)
    value = value.strip()
    return value


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


def normalize_palette(value):
    result = map(
        lambda v: v[0].upper() + '#' + v[1].lower() + ' ' + v[2],
        re_normalize_palette.findall(value)
    )
    if len(result) > 0:
        result.append('')

    return '; '.join(result)


def normalize_threadcount(value, reflect=False):
    result = re.sub('\s', '', value).strip('.').split('.')
    if reflect:
        result = map(
            lambda v: re.sub(re_normalize_threadcount, '\\1/\\2/\\4', v),
            result
        )

    result = map(
        lambda v: re.sub('([0-9]+)', '\\1 ', v).strip(),
        result
    )

    return ' // '.join(filter(len, result)).upper()


def parse_ids():
    result = []

    connection = httplib.HTTPConnection(host)

    # Iterate through all letters
    for letter in [chr(i) for i in range(ord('a'), ord('z') + 1)]:
        path = '/house/' + letter + '.asp'
        log_url(path, prefix='Parsing ')
        connection.request('GET', path)
        resp = connection.getresponse()
        log_http_status(resp.status, resp.reason, prefix=' ')
        ids = re_extract_ids.findall(resp.read())
        count = Colors.BOLD + str(len(ids)) + Colors.ENDC
        sys.stderr.write(' found: ' + count + ' ID(s)\n')
        result += ids

    connection.close()

    result = sorted(map(int, list(set(result))))
    count = Colors.BOLD + str(len(result)) + Colors.ENDC
    sys.stderr.write('Total unique ID(s): ' + count + '\n')
    return result


def parse_tartan(tartan_id):
    connection = httplib.HTTPConnection(host)
    path = '/house/TartanViewjs.asp?colr=Def&tnam=' + str(tartan_id)
    log_url(path, prefix='Parsing ')
    connection.request('GET', path)
    resp = connection.getresponse()
    log_http_status(resp.status, resp.reason, ' ', '\n')
    data = resp.read()
    connection.close()

    # Initialize result
    result = {
        'source': 'House of Tartan',
        'id': tartan_id,
        'category': '',
        'name': '',
        'palette': '',
        'threadcount': '',
        'overview': '',
        'comment': '',
        'copyright': '',
        'updated': now()
    }

    # Parse attributes
    attr = re_extract_attr.findall(data)
    for item in attr:
        result[attr_map[item[0]]] = cleanup_str(item[1])

    # Parse category
    category = re_extract_category.search(result['name'])
    if category:
        result['category'] = category.group(1)
        if not re.search('^[A-Z].+$', result['category']):
            result['category'] = ''

    # Parse pattern components
    pattern = re_extract_pattern.search(data)
    if pattern:
        pattern = json.loads('[' + cleanup_str(pattern.group(1)) + ']')
        result['threadcount'] = normalize_threadcount(
            pattern[0],
            # P - Pivoting, R - Repeating, W - ? (but also repeat)
            pattern[2] == 'P')
        result['palette'] = normalize_palette(pattern[1])

    return result


def main():
    header = Colors.HEADER + 'House of Tartan (' + host + ')' + Colors.ENDC
    sys.stderr.write(header + '\n')
    sys.stderr.write(Colors.OKBLUE + 'Started...' + Colors.ENDC + '\n')
    sys.stdout.write(bom)
    print_csv_row(csv_headers)
    for tartan_id in parse_ids():
        print_csv_row(parse_tartan(tartan_id))
    sys.stderr.write(Colors.OKBLUE + 'Finished.' + Colors.ENDC + '\n')


main()
