import ntpath
import re
import os
import csv
import utils


def get_csv_headers(filename):
    with open(filename) as f:
        if f.read(3) != utils.BOM:
            f.seek(0)
        reader = csv.reader(
            f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL,
            skipinitialspace=True
        )
        row = next(reader, None)
    if row is None:
        return None
    return map(lambda x: (x, title_to_name(x)), row)


def get_csv_records_count(filename):
    with open(filename) as f:
        reader = csv.reader(
            f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL,
            skipinitialspace=True
        )
        return len(list(reader))


def title_to_name(value):
    value = re.sub('[^a-z0-9-_]', '-', value.strip().lower())
    value = re.sub('[-]+', '-', value)
    value = re.sub('[_]+', '_', value)
    return value.strip('-').strip('_')


def create_resource(datafile, **kwargs):
    name = kwargs.get('name', '')
    if name == '':
        name = title_to_name(kwargs.get('title', ''))
    if name == '':
        name = ntpath.splitext(ntpath.basename(datafile))[0].strip()
    title = kwargs.get('title', '')
    if title == '':
        title = name
        title = re.sub('[-_]+', ' ', title).title()

    headers = kwargs.get('headers', None)
    if headers is None:
        headers = get_csv_headers(datafile)
    if headers is None:
        return None
    return {
        'name': name,
        'title': title,
        'path': datafile,
        'format': 'CSV',
        'mediatype': 'text/csv',
        'bytes': os.stat(datafile).st_size,
        'countOfRecords': get_csv_records_count(datafile),
        'schema': {
            'fields': map(
                lambda (index, row): {
                    'name': row[0],
                    'title': row[1],
                    'type':
                        headers[index][2] if len(headers[index]) > 2
                        else 'string',
                    'format': 'default'
                },
                enumerate(headers)
            )
        }
    }


def bump_version(version):
    version = map(int, version.split('.'))
    version[-1] += 1
    return '.'.join(map(str, version))
