from ..core import Source, log, utils
import re
import json
import requests

re_extract_ids = re.compile(
    'onclick="Frm\(\'([0-9]+)\'\)"',
    re.IGNORECASE
)

# 'a'..'z'
catalogue_index = [chr(i) for i in range(ord('a'), ord('z') + 1)]

re_extract_attr = re.compile(
    '<div class="(title|ftr-hdr|ftr-txt|ftr-cpy)">(.*?)</div>',
    re.IGNORECASE | re.DOTALL)

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
        lambda v: v[0].upper() + '#' + v[1].upper() + ' ' + v[2],
        re_normalize_palette.findall(value)
    )
    if len(result) > 0:
        result.append('')

    return '; '.join(result).strip()


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


class HouseOfTartan(Source):

    id = 'house_of_tartan'
    name = 'House of Tartan'

    folders = [
        'index',
        'grabbed'
    ]

    headers = [
        ('origin_id', 'Origin ID', 'string'),
        ('category', 'Category', 'string'),
        ('name', 'Name', 'string'),
        ('palette', 'Palette', 'string'),
        ('threadcount', 'Threadcount', 'string'),
        ('overview', 'Overview', 'string'),
        ('comment', 'Comment', 'string'),
        ('copyright', 'Copyright', 'string'),
        ('origin_url', 'Origin URL', 'string'),
    ]

    resourceAdditionalAttributes = {
        'attributes': {
            'id': 'origin_id',
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
            'description': [
                {'fields': ['overview', 'comment', 'copyright']},
                'filter',
            ],
            'url': 'origin_url',

            'sett': [
                {'fields': ['palette', 'threadcount']},
                'filter',
                {'join': '\n'},
            ],

            'palette': 'palette',
            'threadcount': 'threadcount',

            'overview': 'overview',
            'comment': 'comment',
            'copyright': 'copyright',
        }
    }

    host = 'http://www.house-of-tartan.scotland.net'
    url = 'http://www.house-of-tartan.scotland.net/'

    def get_items(self):
        result = []

        for letter in catalogue_index:
            url = self.host + '/house/' + letter + '.asp'
            log.message('Loading ' + letter + '... ', suffix='')
            resp = requests.get(url)
            log.http_status(resp.status_code, resp.reason, suffix='')
            if resp.status_code == 200:
                self.file_put('index/' + letter + '.html', resp.content)
                ids = re_extract_ids.findall(resp.content)
                result += ids
                log.message(
                    ' found: ' + log.BOLD + str(len(ids)) + log.END + ' ID(s)',
                    suffix=''
                )
            log.newline()

        return sorted(map(int, list(set(result))))

    def retrieve(self, item):
        url = self.host + '/house/TartanViewjs.asp'
        params = {'colr': 'Def', 'tnam': item}
        log.message('Loading ' + str(item), suffix='... ')
        resp = requests.get(url, params=params)
        log.http_status(resp.status_code, resp.reason)
        return self.process_retrieved(
            resp, 'grabbed/' + str(item).zfill(6) + '.html'
        )

    def extract_items(self, item, context):
        log.message('Parsing ' + str(item) + '...')
        result = {}
        data = self.file_get('grabbed/' + str(item).zfill(6) + '.html')
        data = data.decode('utf-8')

        attributes = re_extract_attr.findall(data)
        for attr in attributes:
            result[attr_map[attr[0]]] = utils.cleanup(attr[1])

        # Parse category
        result['category'] = utils.parse_category_from_name(result['name'])
        if result['category'] == '':
            result['category'] = 'Other'

        result['origin_id'] = str(item)
        result['origin_url'] = self.host + '/house/TartanViewjs.asp' + \
            '?colr=Def&tnam=' + str(item)

        # Parse pattern components
        pattern = re_extract_pattern.search(data)
        if pattern:
            pattern = json.loads('[' + utils.cleanup(pattern.group(1)) + ']')
            result['threadcount'] = normalize_threadcount(
                pattern[0],
                # P - Pivoting, R - Repeating, W - ? (but also repeat)
                pattern[2] == 'P')
            result['palette'] = normalize_palette(pattern[1])

        return [result]
