from ..core import Source, log, utils
import re
import json
import requests

re_extract_ids = re.compile(
    'href="tartan_info\.cfm@tartan_id=([0-9]+)\.htm"',
    re.IGNORECASE
)

re_extract_image = re.compile(
    'src="/Tartans/([^."]+\.gif|[^."]+\.jpeg|[^."]+\.jpg|[^."]+\.png)"',
    re.IGNORECASE
)

re_extract_attr = re.compile(
    '<td\s+class="maintext(_nojust)?"[^>]*>(.*?)</td>',
    re.IGNORECASE | re.DOTALL
)

# 'A'..'Z', 'mac'
catalogue_index = [chr(i) for i in range(ord('A'), ord('Z') + 1)] + ['mac']
# catalogue_index = ['Q']


class TartansOfScotland(Source):

    id = 'tartans_of_scotland'
    name = 'Tartans of Scotland'

    folders = [
        'index',
        'grabbed',
        'images'
    ]

    headers = [
        ('origin_id', 'Origin ID', 'string'),
        ('name', 'Name', 'string'),
        ('description', 'Description', 'string'),
        ('category', 'Category', 'string'),
        ('source', 'Source', 'string'),
        ('origin_url', 'Origin URL', 'string'),
    ]

    datapackageAdditionalAttributes = {
        'attributes': [
            {'name': 'id', 'fields': 'origin_id'},
            {'name': 'name', 'fields': 'name'},
            {'name': 'category', 'fields': 'category', 'split': ';'},
            {'name': 'description', 'fields': ['description', 'source']},
            {'name': 'url', 'fields': 'origin_url'},
        ]
    }

    host = 'http://www.tartans.scotland.net'
    url = 'http://www.tartans.scotland.net/'

    def get_items(self):
        result = []

        # Iterate through all letters
        for letter in catalogue_index:
            log.message('Loading ' + letter + '...')
            offset = '1'  # Store offset as string to do less type casts
            while True:
                # For first page we need to put letter before offset
                # really weird
                if offset == '1':
                    url = self.host + '/atoz_returns.cfm' + \
                          '@letter=' + letter + '&startrow=1.htm'
                else:
                    url = self.host + '/atoz_returns.cfm' + \
                          '@startrow=' + offset + \
                          '&letter=' + letter + '.htm'

                resp = requests.get(url)
                if resp.status_code == 200:
                    log.message('offset: ' + offset, prefix='  ', suffix=' ')
                    log.http_status(resp.status_code, resp.reason, suffix='')
                    self.file_put(
                        'index/' + letter + offset.zfill(6) + '.html',
                        resp.content
                    )
                    ids = re_extract_ids.findall(resp.content)
                    result += ids
                    log.message(
                        ' found: ' + log.BOLD + str(len(ids)) +
                        log.END + ' ID(s)',
                        suffix=''
                    )
                log.newline()
                offset = str(int(offset) + 15)
                if resp.status_code == 404:
                    break

        return sorted(map(int, list(set(result))))

    def retrieve(self, item):
        url = self.host + '/tartan_info.cfm@tartan_id=' + str(item) + '.htm'
        log.message('Loading ' + str(item), suffix='... ')
        resp = requests.get(url)
        log.http_status(resp.status_code, resp.reason)

        if resp.status_code == 200:
            images = re_extract_image.findall(resp.content)
            for img in images:
                log.message(img, prefix='  ', suffix=' ')
                url_img = self.host + '/Tartans/' + img
                resp_img = requests.get(url_img)
                log.http_status(resp_img.status_code, resp_img.reason)
                if resp_img.status_code == 200:
                    self.file_put('images/' + img, resp.content)

        return self.process_retrieved(
            resp, 'grabbed/' + str(item).zfill(6) + '.html'
        )

    def extract_items(self, item, context):
        data = self.file_get('grabbed/' + str(item).zfill(6) + '.html')

        result = dict(zip(
            ['name', 'description', 'source'],
            filter(bool, map(
                lambda v: utils.cleanup(v[1]),
                re_extract_attr.findall(data)
            ))
        ))

        if result.get('name', '') == '':
            log.error('item without name: ' + log.BOLD + str(item) + log.END)
            return []

        result['category'] = utils.parse_category_from_name(result['name'])
        if result['category'] == '':
            result['category'] = 'Other'

        result['origin_id'] = str(item)
        result['origin_url'] = \
            self.host + '/tartan_info.cfm@tartan_id=' + \
            str(item) + '.htm'

        return [result]
