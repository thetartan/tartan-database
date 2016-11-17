import os
import argparse
from src.sources.weddslist import Weddslist
from src.sources.house_of_tartan import HouseOfTartan
from src.sources.tartans_authority import TartansAuthority
from src.sources.tartans_of_scotland import TartansOfScotland
from src.sources.register_of_tartans import RegisterOfTartans

source_classes = {
    'weddslist': Weddslist,
    'house-of-tartan': HouseOfTartan,
    'tartans-authority': TartansAuthority,
    'tartans-of-scotland': TartansOfScotland,
    'register-of-tartans': RegisterOfTartans,
}


def get_cli_args():
    wrapper = os.environ.get('__CLI_TOOL_WRAPPER', None)

    parser = argparse.ArgumentParser(
        prog=wrapper,
        description='Tartan database processing tool.'
    )
    parser.add_argument(
        '-g', '--grab', dest='grab', action='store_true',
        help='grab files but do not process them.'
    )
    parser.add_argument(
        '--retry', dest='grab_options', action='append_const', const='retry',
        help='grab option: process only files that has failed or '
             'were skipped in the last session (if any).'
    )
    parser.add_argument(
        '--update', dest='grab_options', action='append_const', const='update',
        help='grab options: grab only new items from source.'
    )
    parser.add_argument(
        '-p', '--parse', dest='parse', action='store_true',
        help='parse grabbed files and generate CSV file(s)'
    )
    parser.add_argument(
        '-d', '--datapackage', dest='datapackage', action='store_true',
        help='update datapackage.json file(s).'
    )
    parser.add_argument(
        'sources', action='store', nargs='+',
        choices=sorted(source_classes.keys()),
        help='source names' if wrapper is None else argparse.SUPPRESS
    )

    args = parser.parse_args()
    if args.grab_options is None:
        args.grab_options = []
    return args


def process_sources(args):
    for source in args.sources:
        source = source_classes[source]()
        if args.grab:
            options = args.grab_options
            source.grab(retry='retry' in options, update='update' in options)
        if args.parse:
            source.parse()
        if args.datapackage:
            source.update_datapackage()


process_sources(get_cli_args())
