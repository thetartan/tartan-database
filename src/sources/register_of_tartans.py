from ..core import Source, log, utils
import re
import ssl
import requests
from requests.adapters import HTTPAdapter


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
    re.IGNORECASE
)

re_form_fields_filled = re.compile(
    '<input\s.*?name="([^"]+)"\s.*value="([^"]*)"',
    re.IGNORECASE
)

re_captcha_image = re.compile(
    '<img\s+.*id="SpamPicture"\s.*src="([^"]+)"',
    re.IGNORECASE
)

re_registration_id = re.compile(
    '/cust_AddNew4\.aspx\?reference=(.+)$',
    re.IGNORECASE
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


class RegisterOfTartans(Source):

    id = 'register_of_tartans'
    name = 'Scottish Register of Tartans'

    folders = [
        'index',
        'meta',
        'threadcount'
    ]

    headers = []

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
            return self.SKIP, None

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
            return self.SKIP, None

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

        return self.SUCCESS, None
