import re
from datetime import datetime
from HTMLParser import HTMLParser

html = HTMLParser()

BOM = '\xEF\xBB\xBF'

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


def now(fmt='%Y/%m/%d %H:%M:%S'):
    return datetime.now().strftime(fmt)


def cleanup(value):
    value = re.sub('(<!--.*?-->|<[^>]*>)', '', value)
    return re.sub('\s+', ' ', html.unescape(value).strip(), flags=re.UNICODE)


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