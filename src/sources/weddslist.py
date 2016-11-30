from ..core import Source, log, utils
import re
import requests

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

categories = [
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
]


def normalize_palette(value):
    result = map(
        lambda v: v[0].upper() + '#' + v[1].upper(),
        re_normalize_palette.findall(value)
    )
    if len(result) > 0:
        result.append('')

    return '; '.join(result).strip()


def normalize_threadcount(value):
    result = re.sub('\s', '', value).strip('(').strip(')')
    result = re.sub(re_normalize_threadcount, '\\1/\\2/\\3', result)

    result = re.sub('\(|\)', '', result)
    result = re.sub('([0-9]+)', '\\1 ', result).strip()

    return result.upper()


def parse_tartan(tartan):
    result = {}
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


class Weddslist(Source):

    id = 'weddslist'
    name = 'Weddslist'

    folders = [
        'grabbed'
    ]

    headers = [
        ('category', 'Category', 'string'),
        ('name', 'Name', 'string'),
        ('palette', 'Palette', 'string'),
        ('threadcount', 'Threadcount', 'string'),
        ('origin_url', 'Origin URL', 'string'),
    ]

    datapackageAdditionalAttributes = {
        'attributes': {
            'name': 'name',
            'category': [
                {'fields': 'category'},
                {'join': ';'},
                {'split': ';'},
                'trim',
                'filter',
                'unique',
                {'sort': 'asc'},
            ],
            'url': 'origin_url',

            'sett': [
                {'fields': ['palette', 'threadcount']},
                'filter',
                {'join': '\n'},
            ],
            'palette': 'palette',
            'threadcount': 'threadcount',
        }
    }

    url = 'http://www.weddslist.com/tartans/links.html'

    def get_items(self):
        return map(lambda c: c['id'], categories)

    def retrieve(self, item):
        url = 'http://www.weddslist.com/cgi-bin/tartans/pg.pl'
        params = {'source': item}
        log.message('Loading ' + item, suffix='... ')
        resp = requests.get(url, params=params)
        log.http_status(resp.status_code, resp.reason)
        return self.process_retrieved(resp, 'grabbed/' + item + '.html')

    def extract_items(self, category, context):
        category = next((x for x in categories if x['id'] == category), None)
        log.message('Parsing ' + category['id'] + '...')
        result = []
        data = self.file_get('grabbed/' + category['id'] + '.html')

        tartans = re_extract_tartans.findall(data)
        for tartan in tartans:
            item = parse_tartan(tartan[0])
            item['category'] = category['name']
            item['comment'] = category['comment']
            item['name'] = utils.cleanup(tartan[1])
            item['origin_url'] = \
                'http://www.weddslist.com/cgi-bin/tartans/pg.pl' + \
                '?source=' + category['id']
            result.append(item)

        return result
