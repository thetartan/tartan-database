import os
import sys
import json
import log
import csvfile as csv
import datapackage
import utils

__dir__ = os.path.dirname(os.path.abspath(__file__))


class Source(object):

    SUCCESS = 'success'
    SKIP = 'skip'
    FAIL = 'fail'

    id = ''
    name = ''
    description = ''
    storage = ''

    folders = []  # folders to be created automatically

    headers = [] # CSV file headers

    url = None

    def __init__(self):
        self.storage = os.path.realpath(os.path.join(
            __dir__, '..', '..', 'storage', self.id
        ))

    def realpath(self, filename):
        if not os.path.exists(self.storage):
            os.makedirs(self.storage)
        for path in self.folders:
            path = os.path.join(self.storage, path)
            if not os.path.exists(path):
                os.makedirs(path)
        return os.path.realpath(os.path.join(self.storage, filename))

    def file_put(self, filename, data):
        with open(self.realpath(filename), 'w') as f:
            f.write(data)

    def file_get(self, filename):
        with open(self.realpath(filename), 'r') as f:
            return f.read()

    def get_items(self):
        return []

    def process_retrieved(self, response, filename):
        if response.status_code == 200:
            self.file_put(filename, response.content)
            return self.SUCCESS, None
        result = (response.status_code, response.reason, response.content)
        if int(response.status_code / 100) in [2, 3]:
            return self.SKIP, result
        return self.FAIL, result

    def retrieve(self, item):
        return self.SKIP, None

    def grab(self):
        log.header(self.name)
        if self.description != '':
            log.subheader(self.description)

        log.started()

        log.started('Initialize queue...')
        items = self.get_items()
        log.message(log.BOLD + str(len(items)) + log.END + ' item(s) in queue')
        result = {
            'all': items,
        }

        log.started('Retrieve data...')
        for item in items:
            status, data = self.retrieve(item)
            temp = result.get(status, [])
            temp.append((item, data))
            result[status] = temp

        log.newline()
        log.subheader('Report:')
        log.notice(
            prefix='  ' + str(len(result['all'])),
            message='item(s) total'
        )
        if len(result.get(self.SUCCESS, [])) > 0:
            log.success(
                prefix='  ' + str(len(result[self.SUCCESS])),
                message='item(s) processed'
            )
        if len(result.get(self.SKIP, [])) > 0:
            log.warning(
                prefix='  ' + str(len(result[self.SKIP])),
                message='item(s) skipped'
            )
        if len(result.get(self.FAIL, [])) > 0:
            log.error(
                prefix='  ' + str(len(result[self.FAIL])),
                message='item(s) failed'
            )
        log.newline()

        log.finished()

        self.file_put('items.json', json.dumps(
            result, sort_keys=True, indent=2, separators=(',', ': ')
        ))

        return result

    def extract_items(self, item, meta):
        return []

    def post_parse(self, items, context):
        return items

    def parse(self, write='data.csv'):
        log.header(self.name)
        if self.description != '':
            log.subheader(self.description)

        log.started()

        items = json.loads(self.file_get('items.json'))
        items = items['all']
        log.message(log.BOLD + str(len(items)) + log.END + ' item(s) in queue')

        context = {}
        result = []
        for item in items:
            result += self.extract_items(item, context)
        result = self.post_parse(result, context)

        if write:
            write = sys.stdout if write is True else write
            write = open(self.realpath(write), 'w') \
                if isinstance(write, basestring) else write
            if len(result) > 0:
                csv.Writer(self.headers, write).write(result)
            if write.name:
                self.update_datapackage(write.name)

        log.newline()
        log.subheader('Report:')
        log.notice(
            prefix='  ' + str(len(items)),
            message='source item(s)'
        )
        log.success(
            prefix='  ' + str(len(result)),
            message='parsed item(s)'
        )
        log.newline()

        log.finished()

        return result

    def update_datapackage(self, datafile='data.csv', additional_meta=None):
        try:
            package = json.loads(self.file_get('datapackage.json'))
        except (IOError, ValueError):
            package = {}

        package['title'] = package.get('title', self.name + ' Tartan Database')
        package['name'] = package.get(
            'name', datapackage.title_to_name(package['title'])
        )

        if additional_meta is not None:
            for key in additional_meta:
                package[key] = additional_meta[key];

        url = self.url if isinstance(self.url, basestring) else ''
        url = ' (' + url + ')' if url != '' else ''
        package['description'] = package.get(
            'description',
            'Database of tartan threadcounts from ' + self.name + url
        )

        resource = datapackage.create_resource(
            self.realpath(datafile)
        )
        prefix = utils.commonprefix([
            resource['path'], self.realpath('datapackage.json')
        ])
        resource['path'] = os.path.relpath(resource['path'], prefix + '/')
        resource['headers'] = True
        package['resources'] = [resource]

        package['author'] = os.environ.get(
            'DATASET_AUTHOR',
            package.get('author', '')
        )
        package['version'] = os.environ.get(
            'DATASET_VERSION',
            datapackage.bump_version(package.get('version', '0.0.0'))
        )

        self.file_put('datapackage.json', json.dumps(
            package, sort_keys=True, indent=2, separators=(',', ': ')
        ) + '\n')
