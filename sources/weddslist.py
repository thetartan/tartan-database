import re
import utils

# Predefined things

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

categories = (
    {
        'id': 'rb',
        'name': 'Robert Bradford',
        'comment': 'Patterns kindly provided by Robert Bradford.',
    },
    {
        'id': 'tinsel',
        'name': 'Thomas Insel',
        'comment': 'Patterns from [Thomas Insel\'s Tartan for Java]'
                   '(http://www.tinsel.org/tinsel/Java/Tartan/setts.txt).',
    },
    {
        'id': 'x',
        'name': 'Jim McBeath & Joseph Shelby',
        'comment': 'Patterns from [XTartan]'
                   '(http://www.io.com/~acroyear/XTartan.html) '
                   'by Jim McBeath & Joseph Shelby.',
    },
    {
        'id': 'sts',
        'name': 'Scottish Tartans Society',
        'comment': 'Patterns from the [Scottish Tartans Society]'
                   '(http://www.scottish-tartans-society.co.uk/).',
    },
    {
        'id': 'misc',
        'name': 'Miscellaneous',
        'comment': 'Patterns from:\n'
                   '1. [wyellowstone.com](http://wyellowstone.com)\n'
                   '2. [House of Tartan]'
                   '(http://www.house-of-tartan.scotland.net/)\n'
                   '3. The Laing Family Tartan\n'
                   '4. The Traill Family Tartan\n'
                   '5. [Ruxton Tartans]'
                   '(http://www.dhs.kyutech.ac.jp/~ruxton/ruxtartans.html)\n'
                   '6. *Programmable plaid: the search for seamless '
                   'integration in fashion and technology*, Bigger & Fraguada',
    },
)


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
    result = utils.new_tartan()
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


def parse_tartans(connection, category):
    path = '/cgi-bin/tartans/pg.pl?source=' + str(category['id'])
    utils.log_url(path, prefix='Parsing ')
    connection.request('GET', path)
    resp = connection.getresponse()
    utils.log_http_status(resp.status, resp.reason, prefix=' ')
    data = resp.read()

    result = []

    tartans = re_extract_tartans.findall(data)
    for tartan in tartans:
        item = parse_tartan(tartan[0])
        item['category'] = category['name']
        item['category_id'] = category['id']
        item['comment'] = category['comment']
        item['name'] = tartan[1].strip()
        item['url'] = path
        result.append(item)

    count = utils.Colors.BOLD + str(len(result)) + utils.Colors.ENDC
    utils.log_message(' found ' + count + ' item(s)\n')

    return result


def main(name, host):
    utils.log_source(name + ' (' + host + ')')
    utils.log_started()
    connection = utils.get_connection(host)
    utils.print_csv_headers()
    for category in categories:
        for row in parse_tartans(connection, category):
            row['source'] = name
            row['url'] = 'http://' + host + row['url']
            utils.print_csv_row(row)
    connection.close()
    utils.log_finished()


main('Weddslist', 'www.weddslist.com')
