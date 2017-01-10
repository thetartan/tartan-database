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

    session_save_interval = 1  # Save for each ID; 0 - to save once at the end

    id = ''
    name = ''
    description = ''
    storage = ''

    folders = []  # folders to be created automatically

    headers = []  # CSV file headers

    # Additional attributes to add to datapackage file
    datapackageAdditionalAttributes = {}

    # Additional attributes to add to resource descriptor
    resourceAdditionalAttributes = {}

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
            return self.SUCCESS
        if int(response.status_code / 100) in [2, 3]:
            return self.SKIP
        return self.FAIL

    def retrieve(self, item):
        return self.SKIP

    # retry - load previous session and try to grab skipped/failed items
    # update - load previous session, compare with new index and
    # grab only new items
    def grab(self, retry=False, update=False):
        log.header(self.name)
        if self.description != '':
            log.subheader(self.description)

        log.started('Starting: grab')

        log.started('Initialize queue...')

        try:
            saved_session = json.loads(self.file_get('items.json'))
        except ValueError:
            saved_session = {'all': []}

        items = self.get_items()

        retry_items = []
        if retry:
            retry_items = saved_session.get(self.SKIP, []) + \
                          saved_session.get(self.FAIL, [])

        update_items = []
        if update:
            processed = saved_session.get(self.SUCCESS, []) + \
                        saved_session.get(self.SKIP, []) + \
                        saved_session.get(self.FAIL, [])
            update_items = [x for x in items if x not in processed]

        queue = retry_items + update_items
        if not retry and not update:
            queue += items

        log.message(log.BOLD + str(len(queue)) + log.END + ' item(s) in queue')
        if retry or update:
            log.error(prefix=str(len(retry_items)), message='item(s) to retry')
            log.warning(prefix=str(len(update_items)), message='new item(s)')

        result = {
            'all': sorted(list(set(items + saved_session.get('all', [])))),
            self.SUCCESS: saved_session.get(self.SUCCESS, [])
        }

        log.started('Retrieve data...')
        queue = sorted(list(set(queue)))
        index = 0
        for item in queue:
            status = self.retrieve(item)
            temp = result.get(status, [])
            temp.append(item)
            result[status] = sorted(list(set(temp)))
            index += 1
            # Save session
            if self.session_save_interval > 0:
                if index % self.session_save_interval == 0:
                    self.file_put('items.json', json.dumps(
                        result, sort_keys=True, indent=2, separators=(',', ': ')
                    ))

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

        log.finished('Finished: grab')
        log.newline()

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

        log.started('Starting: parse')

        items = json.loads(self.file_get('items.json'))
        items = items['all']
        log.message(log.BOLD + str(len(items)) + log.END + ' item(s) in queue')

        context = {}
        result = []
        for item in items:
            result += self.extract_items(item, context)
        result = self.post_parse(result, context)

        if write:
            log.started('Writing CSV data...')
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

        log.finished('Finished: parse')
        log.newline()

        return result

    def update_datapackage(self, datafile='data.csv'):
        log.header(self.name)
        if self.description != '':
            log.subheader(self.description)

        log.started('Starting: update datapackage.json')

        try:
            package = json.loads(self.file_get('datapackage.json'))
            log.success(
                prefix='Load:',
                message=self.realpath('datapackage.json')
            )
        except (IOError, ValueError):
            package = {}
            log.warning('new datapackage will be created.')

        package['title'] = package.get('title', self.name + ' Tartan Database')
        package['name'] = package.get(
            'name', datapackage.title_to_name(package['title'])
        )

        if isinstance(self.datapackageAdditionalAttributes, dict):
            package.update(self.datapackageAdditionalAttributes)

        url = self.url if isinstance(self.url, basestring) else ''
        url = ' (' + url + ')' if url != '' else ''
        package['description'] = package.get(
            'description',
            'Database of tartan threadcounts from ' + self.name + url
        )
        package['author'] = os.environ.get(
            'DATASET_AUTHOR',
            package.get('author', '')
        )
        package['version'] = os.environ.get(
            'DATASET_VERSION',
            datapackage.bump_version(package.get('version', '0.0.0'))
        )

        package['updated'] = utils.now()
        resource = datapackage.create_resource(
            self.realpath(datafile), headers=self.headers, title=self.name
        )
        if resource is not None:
            prefix = utils.commonprefix([
                resource['path'], self.realpath('datapackage.json')
            ])
            resource['path'] = os.path.relpath(resource['path'], prefix + '/')
            resource['headers'] = True

            items = json.loads(self.file_get('items.json'))
            count_of_records = len(items.get('success', []))
            if count_of_records > 0:
                resource['countOfRecords'] = count_of_records

            if isinstance(self.resourceAdditionalAttributes, dict):
                resource.update(self.resourceAdditionalAttributes)

            package['resources'] = [resource]

            self.file_put('datapackage.json', json.dumps(
                package, sort_keys=True, indent=2, separators=(',', ': ')
            ) + '\n')

            log.success(
                prefix='Saved:',
                message=self.realpath('datapackage.json')
            )

        log.finished('Finished: update datapackage.json')
        log.newline()
