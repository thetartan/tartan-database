import sys
import datetime
import httplib
import re
import csv
from HTMLParser import HTMLParser
html = HTMLParser()

# Predefined things
host = 'www.weddslist.com'

bom = '\xEF\xBB\xBF'

re_extract_tartans = re.compile(
    '<option\s+value="([^"]*)">([^<]*)',
    re.IGNORECASE)

re_extract_palette = re.compile(
    '^(([a-z]*#[0-9a-f]{6})*)(\[|\]|$)',
    re.IGNORECASE
)

re_extract_warp = re.compile(
    '\[(([a-z]+[0-9]+|\(|\))*)(\]|$)',
    re.IGNORECASE
)

re_extract_weft = re.compile(
    '\](([a-z]+[0-9]+|\(|\))*)(\[|$)',
    re.IGNORECASE
)

re_normalize_palette = re.compile(
    '([a-z]+)#([0-9a-f]{6})',
    re.IGNORECASE
)

re_normalize_threadcount = re.compile(
    '^([a-z]+)([0-9]+\([a-z0-9]+\)[a-z]+)([0-9]+)$',
    re.IGNORECASE
)

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


categories = (
    ('rb', 'Robert Bradford'),
    ('tinsel', 'Thomas Insel'),
    ('x', 'Jim McBeath & Joseph Shelby'),
    ('sts', 'Scottish Tartans Society'),
    ('misc', 'Miscellaneous'),
)


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
        lambda v: v[0].upper() + '#' + v[1].lower(),
        re_normalize_palette.findall(value)
    )
    if len(result) > 0:
        result.append('')

    return '; '.join(result)


def normalize_threadcount(value):
    result = re.sub('\s', '', value).strip('(').strip(')')
    result = re.sub(re_normalize_threadcount, '\\1/\\2/\\3', result)

    result = re.sub('\(|\)', '', result)
    result = re.sub('([0-9]+)', '\\1 ', result).strip()

    return result.upper()


def parse_tartan(tartan):
    # Initialize result
    result = {
        'source': 'Weddslist',
        'id': '',
        'category': '',
        'name': '',
        'palette': '',
        'threadcount': '',
        'overview': '',
        'comment': '',
        'copyright': '',
        'updated': now()
    }

    tartan = tartan.strip()

    # Extract palette, warp and weft sequences
    temp = re_extract_palette.search(tartan)
    if temp:
        result['palette'] = normalize_palette(temp.group(1))

    warp = ''
    weft = ''
    temp = re_extract_warp.search(tartan)
    if temp:
        warp = normalize_threadcount(temp.group(1))
    temp = re_extract_weft.search(tartan)
    if temp:
        weft = normalize_threadcount(temp.group(1))

    if weft == warp:
        weft = ''

    result['threadcount'] = ' // '.join(filter(len, [warp, weft]))

    return result


def parse_tartans(category_id, category_name):
    connection = httplib.HTTPConnection(host)
    path = '/cgi-bin/tartans/pg.pl?source=' + str(category_id)
    log_url(path, prefix='Parsing ')
    connection.request('GET', path)
    resp = connection.getresponse()
    log_http_status(resp.status, resp.reason, prefix=' ')
    data = resp.read()
    connection.close()

    result = []

    tartans = re_extract_tartans.findall(data)
    for tartan in tartans:
        item = parse_tartan(tartan[0])
        item['category'] = category_name
        item['name'] = tartan[1].strip()
        result.append(item)

    count = Colors.BOLD + str(len(result)) + Colors.ENDC
    sys.stderr.write(' found ' + count + ' item(s)\n')

    return result


def main():
    header = Colors.HEADER + 'Weddslist (' + host + ')' + Colors.ENDC
    sys.stderr.write(header + '\n')
    sys.stderr.write(Colors.OKBLUE + 'Started...' + Colors.ENDC + '\n')
    sys.stdout.write(bom)
    print_csv_row(csv_headers)
    for category in categories:
        for row in parse_tartans(category[0], category[1]):
            print_csv_row(row)
    sys.stderr.write(Colors.OKBLUE + 'Finished.' + Colors.ENDC + '\n')


main()
