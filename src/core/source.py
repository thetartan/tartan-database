import os
import sys
import json
import log
import csvfile as csv

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

    headers = []

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

    def extract_items(self, item):
        return []

    def parse(self, write='data.csv'):
        log.header(self.name)
        if self.description != '':
            log.subheader(self.description)

        log.started()

        items = json.loads(self.file_get('items.json'))
        items = items['all']
        log.message(log.BOLD + str(len(items)) + log.END + ' item(s) in queue')

        result = []
        for item in items:
            result += self.extract_items(item)

        if write:
            write = sys.stdout if write is True else write
            write = open(self.realpath(write), 'w') \
                if isinstance(write, basestring) else write
            if len(result) > 0:
                csv.Writer(self.headers, write).write(result)

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
