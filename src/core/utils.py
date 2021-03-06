import re
import random
import string
from datetime import datetime
from PIL import ImageColor
from HTMLParser import HTMLParser

html = HTMLParser()

BOM = '\xEF\xBB\xBF'

re_words = re.compile('[a-z]{3,}', re.IGNORECASE)

stop_words = ['the', 'for', 'and']  # Two-letter words ignored by regex

remap_dictionary = {
    'schools': 'school',
    'artefact': 'artifact',
    'assoc': 'association',
    'regiment': 'regimental',
    'univ': 'universal',
    'sports': 'sport',
    'weaver': 'weavers',
    'restrticted': 'restricted',
    'malay': 'malaysian',
    'indan': 'indian',
    'germany': 'german',
    'distrtict': 'district',
    'caanadian': 'canadian',

    'commemorarive': 'commemorative',
    'comemmorative': 'commemorative',
    'commemmorative': 'commemorative',
    'com': 'commemorative',
    'comm': 'commemorative',
    'commem': 'commemorative',

    'coprorate': 'corporate',
    'corparate': 'corporate',
    'corpoarate': 'corporate',
    'corpoate': 'corporate',
    'corppoate': 'corporate',
    'corpporate': 'corporate',
    'corprate': 'corporate',

    'fashin': 'fashion',
    'dashion': 'fashion',

    'portrair': 'portrait',
    'portrat': 'portrait',

    'peronal': 'personal',
    'perposnal': 'personal',
    'personnal': 'personal',

    'pipeband': 'pipers',
    'pipes': 'pipers',
    'pipe': 'pipers',

    'uncategorised': 'other',
    'unidentfied': 'other',
    'unidentieid': 'other',
    'unidentified': 'other',
    'unidientified': 'other',
    'unknown': 'other',
    'unnamed': 'other',

    'misc': 'other',
    'new': 'other',
    'non': 'other',
    'not': 'other',
}

change_case = {
    'uae': 'UAE',
}

def now(fmt='%Y/%m/%d %H:%M:%S'):
    return datetime.now().strftime(fmt)


def cleanup(value):
    value = re.sub(
        '(<!--.*?-->|<[^>]*>)', '', value,
        flags=re.UNICODE | re.DOTALL
    )
    return re.sub('\s+', ' ',
        html.unescape(value).strip(),
        flags=re.UNICODE)


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


def parse_category_from_name(name, delimiter='; '):
    words = extract_words(name)
    result = []
    if (len(words) > 0) and (words[0] not in allowed_categories):
        del words[0]
    for word in words:
        if word in allowed_categories:
            result.append(change_case.get(word, word.title()))
        else:
            break
    result.reverse()
    result = sorted(list(set(result)))
    return delimiter.join(result)


def parse_category(value, delimiter='; '):
    result = map(
        lambda v: change_case.get(v, v.title()),
        sorted(list(set(extract_words(value))))
    )
    return delimiter.join(result)


def commonprefix(l):
    # this unlike the os.path.commonprefix version
    # always returns path prefixes as it compares
    # path component wise
    cp = []
    ls = [p.split('/') for p in l]
    ml = min( len(p) for p in ls )

    for i in range(ml):

        s = set( p[i] for p in ls )
        if len(s) != 1:
            break

        cp.append(s.pop())

    return '/'.join(cp)


def html_adjust(color, factor):
    return '#' + ''.join(map(
        lambda v: '%02x' % min(int(v * factor), 255),
        ImageColor.getrgb(color)
    )).upper()


def html_mix(*colors):
    return '#' + ''.join(map(
        lambda v: '%02x' % int(sum(v) / len(v)),
        zip(*map(ImageColor.getrgb, colors))
    )).upper()


def adjust_color(name, palette, default='%%'):
    adjust = {'L': 1.0 + 1.0/3.0, 'D': 1.0 - 1.0/3.0}
    result = palette.get(name, '')
    if result != '':
        return result

    prefix = name[0].upper()
    if prefix in ['L', 'D']:
        name = name[1:]

    result = palette.get(name, '')
    if result == '':
        result = html_mix(*[x for x in map(
            lambda c: palette.get(c, ''),
            name
        ) if x != '']) + default

    if result != '':
        if prefix in adjust:
            return html_adjust(result, adjust[prefix])
        return result

    return default


def random_item(items):
    return random.choice(items)


def random_string(chars, min=6, max=20):
    return ''.join(random.choice(chars) for x in range(min, max))


def random_letters(min=6, max=20):
    return random_string(string.ascii_letters, min, max)


def random_lower(min=6, max=20):
    return random_string(string.ascii_lowercase, min, max)


def random_upper(min=6, max=20):
    return random_string(string.ascii_uppercase, min, max)


def random_digits(min=3, max=10):
    return random_string(string.digits, min, max)
