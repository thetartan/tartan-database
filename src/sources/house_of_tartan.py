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

# Used to parse category from name

re_words = re.compile('[a-z]{3,}', re.IGNORECASE)

stop_words = ['the', 'for', 'and']  # Two-letter words ignored by regex

remap_dictionary = {
    'comemmorative': 'commemorative',
    'commemmorative': 'commemorative',
    'com': 'commemorative',
    'comm': 'commemorative',
    'commem': 'commemorative',
    'schools': 'school',
    'artefact': 'artifact',
    'assoc': 'association',
    'regiment': 'regimental',
    'univ': 'universal',
    'sports': 'sport',
}

allowed_categories = [
    # Administrative
    'city', 'county', 'district', 'state', 'country',
    # Category
    'ancient', 'artifact',  'commemorative', 'corporate', 'dance', 'design',
    'dress', 'fancy', 'fashion', 'general', 'hunting', 'plaid', 'portrait',
    'universal', 'gathering',
    # Activity and organizations
    'band', 'club', 'national', 'international', 'regimental', 'royal',
    'school', 'trade', 'sport', 'university', 'weavers', 'academy',
    'association',
    # Person
    'clan', 'family', 'name', 'personal',
]


def remap_word(word):
    while True:
        new = remap_dictionary.get(word, None)
        if new is None:
            break
        word = new
    return word


def extract_words(value):
    words = re_words.findall(value.lower())
    words.reverse()
    if (len(words) > 0) and (words[0] == 'tartan'):
        del words[0]
    return filter(len, [remap_word(x) for x in words if x not in stop_words])


def parse_category(name, delimiter='; '):
    words = extract_words(name)
    result = []
    if (len(words) > 0) and (words[0] not in allowed_categories):
        del words[0]
    for word in words:
        if word in allowed_categories:
            result.append(word.title())
        else:
            break
    result.reverse()
    result = sorted(list(set(result)))
    return delimiter.join(result)


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
        ('source', 'Source'),
        ('id', 'Source ID'),
        ('category', 'Category'),
        ('name', 'Name'),
        ('palette', 'Palette'),
        ('threadcount', 'Threadcount'),
        ('overview', 'Overview'),
        ('comment', 'Comment'),
        ('copyright', 'Copyright'),
        ('url', 'Source URL'),
    ]

    host = 'http://www.house-of-tartan.scotland.net'

    def get_items(self):
        result = []

        # Iterate through all letters
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

    def extract_items(self, item):
        log.message('Parsing ' + str(item) + '...')
        result = {}
        data = self.file_get('grabbed/' + str(item).zfill(6) + '.html')

        attributes = re_extract_attr.findall(data)
        for attr in attributes:
            result[attr_map[attr[0]]] = utils.cleanup(attr[1])

        # Parse category
        result['category'] = parse_category(result['name'])
        if result['category'] == '':
            result['category'] = 'Other'

        result['source'] = self.name
        result['id'] = str(item)
        result['url'] = self.host + '/house/TartanViewjs.asp' + \
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
