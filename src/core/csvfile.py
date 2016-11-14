import csv
import sys


class Writer:
    BOM = '\xEF\xBB\xBF'

    headers = None
    file = None
    writer = None

    def __init__(self, headers, file=sys.stdout):
        self.headers = headers
        self.file = file
        self.writer = csv.writer(
            file,
            delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL,
            escapechar='\\', doublequote=True
        )

    def write_headers(self, write_bom=True):
        self.write_row(dict(self.headers), write_bom)

    def write_row(self, row, write_bom=False):
        if write_bom:
            self.file.write(self.BOM)
        data = []
        for header in self.headers:
            data.append(unicode(row.get(header[0], '')).encode('utf-8'))
        self.writer.writerow(data)

    def write_rows(self, rows, write_bom=False):
        for row in rows:
            self.write_row(row, write_bom)

    def write(self, rows, write_bom=True):
        self.write_headers(write_bom)
        self.write_rows(rows, False)
