import re
from datetime import datetime
from HTMLParser import HTMLParser

html = HTMLParser()


def now(fmt='%Y/%m/%d %H:%M:%S'):
    return datetime.now().strftime(fmt)


def cleanup(value):
    value = re.sub('(<!--.*?-->|<[^>]*>)', '', value)
    return re.sub('\s+', ' ', html.unescape(value).strip(), flags=re.UNICODE)
