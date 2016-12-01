from ..core import Source, log, utils
import re
import ssl
import requests
from requests.adapters import HTTPAdapter

# This Register of Tartans site forces https, but we should
# use TLSv1 - otherwise server will not reply to SSL handshake.
# Also their IIS may fail with strange errors, so handle it
# carefully

class ForceTLSV1Adapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        # This method gets called when there's no proxy.
        pool_kwargs['ssl_version'] = ssl.PROTOCOL_TLSv1
        return super(ForceTLSV1Adapter, self).init_poolmanager(
            connections, maxsize, block, **pool_kwargs
        )


# 'a'..'z'
catalogue_index = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

re_form_fields_all = re.compile(
    '<input\s.*?name="([^"]+)"',
    re.IGNORECASE | re.DOTALL | re.UNICODE
)

re_form_fields_filled = re.compile(
    '<input\s.*?name="([^"]+)"\s.*value="([^"]*)"',
    re.IGNORECASE | re.DOTALL | re.UNICODE
)

re_captcha_image = re.compile(
    '<img\s+.*id="SpamPicture"\s.*src="([^"]+)"',
    re.IGNORECASE | re.DOTALL | re.UNICODE
)

re_registration_id = re.compile(
    '/cust_AddNew4\.aspx\?reference=(.+)$',
    re.IGNORECASE | re.DOTALL
)

re_extract_attr = re.compile(
    '<tr>\s*<td\s+class="coreTextBold"[^>]*>(.*?)</td>\s*'
    '<td\s+class="coreText"[^>]*>(.*?)</td>\s*</tr>',
    re.IGNORECASE | re.DOTALL | re.UNICODE
)

captcha = {
    'images/scam_filter/1.jpg': 'Haggis',
    'images/scam_filter/2.jpg': 'Candy',
    'images/scam_filter/3.jpg': 'Garden',
    'images/scam_filter/4.jpg': 'TigerLily',
    'images/scam_filter/5.jpg': 'Bubble',
    'images/scam_filter/6.jpg': 'Rainbow',
    'images/scam_filter/7.jpg': 'Stars',
    'images/scam_filter/8.jpg': 'Dolphin',
    'images/scam_filter/9.jpg': 'Dance',
    'images/scam_filter/10.jpg': 'Flower',
}

re_extract_ids = re.compile(
    'href="tartanDetails\.aspx\?ref=([0-9]+)"',
    re.IGNORECASE
)

attr_map = {
    'Category': 'category',
    'Restrictions': 'restrictions',
    'Designer': 'source',
    'STA ref:': 'sta_ref',  # 'none' -> ''
    'STWR ref:': 'stwr_ref',  # 'none' -> ''
    'Woven Sample:': 'woven_sample',
    'Registration notes': 'notes',
    'Tartan date': 'date',
    'Information notes:': 'comment',  # 'Not Specified' -> ''
    'Registration date': 'registration_date',
    'Reference:': '',  # remove - it is `origin_id`
    'Registrant details:': 'registrant_details'
}

re_extract_threadcount_block = re.compile(
    '<span\s+id="lblResults">.*?<table(.+?)</table>',
    re.IGNORECASE | re.DOTALL | re.UNICODE
)

re_extract_threadcount = re.compile(
    '<tr[^>]*?>.*?href="tartanDetails\.aspx\?ref=([0-9]+)".*?>(.+?)</a>.*?'
    '<td>(.*?)</td>.*?</tr>',
    re.IGNORECASE | re.DOTALL | re.UNICODE
)


def parse_attributes(data):
    result = dict(filter(
        lambda (key, value): key != '',
        map(
            lambda (key, value): (
                attr_map[
                    utils.cleanup(key.strip().strip(':'))
                ] if key != '' else '',
                utils.cleanup(value.decode('utf-8'))
            ),
            re_extract_attr.findall(data)
        )
    ))

    result['category'] = utils.parse_category(result.get('category', ''))
    if result['category'] == '':
        result['category'] = 'Other'

    if 'sta_ref' in result:
        if result['sta_ref'].lower() == 'none':
            result['sta_ref'] = ''

    if 'stwr_ref' in result:
        if result['stwr_ref'].lower() == 'none':
            result['stwr_ref'] = ''

    if 'comment' in result:
        if result['comment'].lower() == 'not specified':
            result['comment'] = ''

    return result


re_normalize_palette = re.compile(
    '([a-z]+)=([0-9a-f]{6})([a-z\s()]*)[;,]',
    re.IGNORECASE | re.DOTALL
)

re_normalize_threadcount = re.compile(
    '^([a-z]+)([0-9]+([a-z]+[0-9]+)+[a-z]+)([0-9]+)$',
    re.IGNORECASE
)


def normalize_palette(value):
    result = map(
        lambda v: v[0].upper() + '#' + v[1].upper() + ' ' + v[2],
        re_normalize_palette.findall(';' + value + ';')
    )
    if len(result) > 0:
        result.append('')

    return '; '.join(result).strip()


def normalize_threadcount(value, reflect=False):
    result = map(
        lambda v: re.sub('[^a-zA-Z0-9]+', '', v),
        value.strip('.').split('.')
    )
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


def parse_threadcount(item, data):
    data = ''.join(re_extract_threadcount_block.findall(data))
    result = dict(map(
        lambda x: (x[0], (x[1], x[2])),
        re_extract_threadcount.findall(data)
    )).get(str(item), '')

    name = result[0]
    result = result[1]

    result = filter(
        bool,
        re.sub('<br>', '%%', result, flags=re.IGNORECASE).split('%%')
    )
    if len(result) <= 1:
        return {}

    # type can be:
    # - reflective
    #   'Threadcount given over a half sett with full count at the pivots.'
    # - repetitive
    #   'Threadcount given over the full sett.'
    is_reflective = 'half sett' in utils.cleanup(result[0]).lower()

    threadcount = normalize_threadcount(result[1], is_reflective)
    palette = utils.cleanup(result[2] if len(result) >= 3 else '')
    if palette.lower() == 'not specified':
        palette = ''

    return {
        'name': utils.cleanup(name.decode('utf-8')),
        'threadcount': threadcount,
        'palette': normalize_palette(palette),
    }


class RegisterOfTartans(Source):

    id = 'register_of_tartans'
    name = 'Scottish Register of Tartans'

    folders = [
        'index',
        'meta',
        'threadcount'
    ]

    headers = [
        ('origin_id', 'Origin ID', 'string'),
        ('category', 'Category', 'string'),
        ('name', 'Name', 'string'),
        ('palette', 'Palette', 'string'),
        ('threadcount', 'Threadcount', 'string'),
        ('restrictions', 'Restrictions', 'string'),
        ('source', 'Source', 'string'),
        ('sta_ref', 'STA Reference', 'string'),
        ('stwr_ref', 'STWR Reference', 'string'),
        ('woven_sample', 'Wowen Sample', 'string'),
        ('notes', 'Notes', 'string'),
        ('date', 'Date', 'string'),
        ('comment', 'Comment', 'string'),
        ('registration_date', 'Registration Date', 'string'),
        ('registrant_details', 'Registrant details', 'string'),
        ('origin_url', 'Origin URL', 'string'),
    ]

    datapackageAdditionalAttributes = {
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
            'url': 'origin_url',
            'description': [
                {'fields': ['comment', 'notes', 'restrictions',
                            'source', 'woven_sample']},
                'filter',
            ],
            'sett': [
                {'fields': ['palette', 'threadcount']},
                'filter',
                {'join': '\n'},
            ],
            'palette': 'palette',
            'threadcount': 'threadcount',

            'STAReference': 'sta_ref',
            'STWRReference': 'stwr_ref',
            'date': 'date',
            'registrationDate': 'registration_date',
            'registrantDetails': 'registrant_details',
        }
    }

    host = 'https://www.tartanregister.gov.uk'
    url = 'https://www.tartanregister.gov.uk/'

    def get_item_username(self, item):
        return 'zorro' + str(item)

    def get_item_password(self, item):
        return 'q1w2e3r4t5'

    def get_item_email(self, item, host='example.com'):
        # return 'wucev@rootfest.net'
        return self.get_item_username(item) + '@' + host

    def get_form_fields(self, content):
        result = re_form_fields_all.findall(content)
        result = dict(zip(result, [''] * len(result)))
        result.update(dict(re_form_fields_filled.findall(content)))
        return result

    def solve_captcha(self, content):
        results = re_captcha_image.findall(content)
        if len(results) > 0:
            return captcha.get(results[0], '')
        return ''

    def login(self, session, item):
        # Initialize ASP session
        resp = session.get(self.host + '/LogIn.aspx')
        if resp.status_code != 200:
            return False
        # Fill form fields
        data = self.get_form_fields(resp.content)
        username = self.get_item_username(item)
        password = self.get_item_password(item)
        data.update({
            'tbxUsername': username,
            'tbxPassword': password
        })
        # Submit and check where we are
        resp = session.post(self.host + '/LogIn.aspx', data=data)
        if resp.url == self.host + '/yourAccount.aspx':
            log.log(username + ':' + password, prefix='Logged as')
            return True
        return False

    def register(self, session, item):
        # Initialize ASP session
        resp = session.get(self.host + '/cust_AddNew1.aspx')
        if resp.status_code != 200:
            return False
        # Fill form fields
        data = self.get_form_fields(resp.content)
        username = self.get_item_username(item)
        password = self.get_item_password(item)
        email = self.get_item_email(item)
        data.update({
            'tbxForename': username,
            'tbxSurname': username,
            'tbxUsername': username,
            'tbxUsernameConfirm': username,
            'tbxPassword': password,
            'tbxPasswordConfirm': password,
            'ddlSecretQuestion': '1',
            'tbxSecretAnswer': username,
            'tbxHouse': utils.random_letters(),
            'tbxStreet1': utils.random_letters(),
            'tbxPostcode': utils.random_digits(),
            'ddlCountryRegion': utils.random_item([
                'Scotland',
                'England',
                'Northern Ireland',
                'Wales'
            ]),
            'tbxEmail': email,
            'tbxEmailConfirm': email,
            'tbxSpamAnswer': self.solve_captcha(resp.content),
        })
        # Submit form
        resp = session.post(self.host + '/cust_AddNew1.aspx', data=data)

        if resp.url != self.host + '/cust_AddNew2.aspx':
            return False
        data = self.get_form_fields(resp.content)
        resp = session.post(self.host + '/cust_AddNew2.aspx', data=data)

        registration_id = re_registration_id.findall(resp.url)
        if len(registration_id) == 0:
            return False
        registration_id = registration_id[0]
        # Registration can fail up to this moment.
        # If user will be registered, but confirmation fails - we will
        # lost this user forever. So display confirmation code - it may be
        # used to activate user manually
        log.notice(username + ' ' + registration_id)

        resp = session.get(
            self.host + '/customerConfirm.aspx',
            params={'ref': registration_id}
        )

        if resp.status_code == 200:
            log.log(username + ':' + password, prefix='Registered as')
            return True
        return False

    def get_session(self, item=None):
        session = requests.Session()
        session.mount('https://', ForceTLSV1Adapter())
        session.headers.update({
            'User-Agent':
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/54.0.2840.59 Safari/537.36'
        })

        if item:
            session.is_logged_in = True
            if not self.login(session, item):
                if not self.register(session, item):
                    session.is_logged_in = False
                    log.error(
                        'failed to register as ' +
                        self.get_item_username(item) + ':' +
                        self.get_item_password(item)
                    )
                if not self.login(session, item):
                    session.is_logged_in = False
                    log.error(
                        'failed to log in as ' +
                        self.get_item_username(item) + ':' +
                        self.get_item_password(item)
                    )

        return session

    def get_items(self):
        result = []

        session = self.get_session()

        for letter in catalogue_index:
            url = self.host + '/az.aspx'
            params = {'searchString': letter}
            log.message('Loading ' + letter + '... ', suffix='')

            resp = session.get(url, params=params)
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
        log.message('Loading ' + str(item) + '...')
        filename = str(item).zfill(6)

        session = self.get_session(item)
        if not session.is_logged_in:
            return self.SKIP

        # Get page info
        resp = session.get(
            self.host + '/tartanDetails.aspx', params={'ref': item}
        )
        log.http_status(
            resp.status_code, resp.reason,
            prefix='  info: '
        )
        if resp.status_code == 200:
            self.file_put('meta/' + filename + '.html', resp.content)
        else:
            return self.SKIP

        # Get threadcount
        session.get(
            self.host + '/threadCountRequest.aspx', params={'ref': item}
        )
        resp = session.get(self.host + '/viewThread.aspx')
        log.http_status(
            resp.status_code, resp.reason,
            prefix='  threadcount: '
        )
        if resp.status_code == 200:
            self.file_put('threadcount/' + filename + '.html', resp.content)

        return self.SUCCESS

    def extract_items(self, item, context):
        log.message('Parsing ' + str(item) + '...')
        data = self.file_get('meta/' + str(item).zfill(6) + '.html')

        result = parse_attributes(data)

        if 'ref' in result:
            print item, result
            exit()

        result['origin_id'] = str(item)
        result['origin_url'] = \
            self.host + '/tartanDetails.aspx?ref=' + str(item)

        data = self.file_get('threadcount/' + str(item).zfill(6) + '.html')
        # `name` is also parsed here!
        result.update(parse_threadcount(item, data))

        return [result]
