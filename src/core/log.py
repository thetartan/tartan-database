import sys

HEADER = '\033[95m'
NOTICE = '\033[94m'
SUCCESS = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
END = '\033[0m'


def error(message, prefix='Error:', suffix='', file=sys.stderr):
    prefix += ' ' if prefix != '' else ''
    file.write(
        BOLD + FAIL + prefix + END +
        FAIL + message + suffix + END + '\n'
    )


def warning(message, prefix='Warning:', suffix='', file=sys.stderr):
    prefix += ' ' if prefix != '' else ''
    file.write(
        BOLD + WARNING + prefix + END +
        WARNING + message + suffix + END + '\n'
    )


def notice(message, prefix='Notice:', suffix='', file=sys.stderr):
    prefix += ' ' if prefix != '' else ''
    file.write(
        BOLD + NOTICE + prefix + END +
        NOTICE + message + suffix + END + '\n'
    )


def success(message, prefix='Success:', suffix='', file=sys.stderr):
    prefix += ' ' if prefix != '' else ''
    file.write(
        BOLD + SUCCESS + prefix + END +
        SUCCESS + message + suffix + END + '\n'
    )


def log(message, prefix='Log:', suffix='', file=sys.stderr):
    prefix += ' ' if prefix != '' else ''
    file.write(BOLD + prefix + END + message + suffix + '\n')


def message(message, prefix='', suffix='\n', file=sys.stderr):
    file.write(prefix + message + suffix)


def newline(file=sys.stderr):
    file.write('\n')


def header(message, file=sys.stderr):
    file.write(BOLD + HEADER + message + END + '\n')


def subheader(message, file=sys.stderr):
    file.write(HEADER + message + END + '\n')


def started(message='Started...', file=sys.stderr):
    file.write(NOTICE + message + END + '\n')


def finished(message='Finished.', file=sys.stderr):
    file.write(NOTICE + message + END + '\n')


def http_status(code, reason, prefix='', suffix='\n', file=sys.stderr):
    color = {
        1: WARNING,
        2: SUCCESS,
        3: WARNING,
        4: FAIL,
        5: FAIL
    }[int(code / 100)]
    file.write(color + prefix + str(code) + ' ' + str(reason) + suffix + END)


def url(url, prefix='', suffix='\n', file=sys.stderr):
    file.write(prefix + UNDERLINE + url + END + suffix)
