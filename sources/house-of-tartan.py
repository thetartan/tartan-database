import re
import json
import utils

# Predefined things
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


def parse_ids(connection):
    result = []

    # Iterate through all letters
    for letter in [chr(i) for i in range(ord('a'), ord('z') + 1)]:
        path = '/house/' + letter + '.asp'
        utils.log_url(path, prefix='Parsing ')
        connection.request('GET', path)
        resp = connection.getresponse()
        utils.log_http_status(resp.status, resp.reason, prefix=' ')
        ids = re_extract_ids.findall(resp.read())
        count = utils.Colors.BOLD + str(len(ids)) + utils.Colors.ENDC
        utils.log_message(' found: ' + count + ' ID(s)\n')
        result += ids

    result = sorted(map(int, list(set(result))))
    count = utils.Colors.BOLD + str(len(result)) + utils.Colors.ENDC
    utils.log_message('Total unique ID(s): ' + count + '\n')
    return result


def parse_tartan(connection, tartan_id):
    path = '/house/TartanViewjs.asp?colr=Def&tnam=' + str(tartan_id)
    utils.log_url(path, prefix='Parsing ')
    connection.request('GET', path)
    resp = connection.getresponse()
    utils.log_http_status(resp.status, resp.reason, ' ', '\n')
    data = resp.read()

    result = utils.new_tartan()
    result['id'] = tartan_id
    result['url'] = path

    # Parse attributes
    attr = re_extract_attr.findall(data)
    for item in attr:
        result[attr_map[item[0]]] = utils.cleanup_str(item[1])

    # Parse category
    result['category'] = utils.parse_category(result['name'])

    # Parse pattern components
    pattern = re_extract_pattern.search(data)
    if pattern:
        pattern = json.loads('[' + utils.cleanup_str(pattern.group(1)) + ']')
        result['threadcount'] = normalize_threadcount(
            pattern[0],
            # P - Pivoting, R - Repeating, W - ? (but also repeat)
            pattern[2] == 'P')
        result['palette'] = normalize_palette(pattern[1])

    return result


def main(name, host):
    utils.log_source(name + ' (' + host + ')')
    utils.log_started()
    connection = utils.get_connection(host)
    utils.print_csv_headers()
    for tartan_id in parse_ids(connection):
        tartan = parse_tartan(connection, tartan_id)
        tartan['url'] = 'http://' + host + tartan['url']
        tartan['source'] = name
        utils.print_csv_row(tartan)
    connection.close()
    utils.log_finished()


main('House of Tartan', 'www.house-of-tartan.scotland.net')
