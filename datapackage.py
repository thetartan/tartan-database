import json
import ntpath
import sys
import re
import os
import csv


def get_schema_fields(filename):
    with open(filename) as f:
        reader = csv.reader(
            f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL,
            skipinitialspace=True
        )
        row = next(reader)
    return map(
        lambda x: {
            'name': title_to_name(x),
            'title': x,
            'type': 'string',
            'format': 'default'
        },
        row
    )


def title_to_name(value):
    value = re.sub('[^a-z0-9-_]', '-', value.strip().lower())
    value = re.sub('[-]+', '-', value)
    value = re.sub('[_]+', '_', value)
    return value.strip('-').strip('_')


def create_resource(filename):
    title = ntpath.splitext(ntpath.basename(filename))[0].strip()
    title = re.sub('[-_]+', ' ', title).title()
    return {
        'name': title_to_name(title),
        'title': title,
        'path': filename,
        'format': 'CSV',
        'mediatype': 'text/csv',
        'bytes': os.stat(filename).st_size,
        'schema': {
            'fields': get_schema_fields(filename)
        }
    }


def bump_version(version):
    version = map(int, version.split('.'))
    version[-1] += 1
    return '.'.join(map(str, version))


def main(data_filename):
    package = json.loads(sys.stdin.read())

    package['name'] = title_to_name(package['title'])
    package['resources'] = [create_resource(data_filename)]
    package['version'] = bump_version(package['version'])

    sys.stdout.write(json.dumps(
        package, sort_keys=True, indent=2, separators=(',', ': ')
    ))


main('database.csv')
