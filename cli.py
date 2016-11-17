import sys
import re
from src.sources.weddslist import Weddslist
from src.sources.house_of_tartan import HouseOfTartan
from src.sources.tartans_authority import TartansAuthority
from src.sources.tartans_of_scotland import TartansOfScotland
from src.sources.register_of_tartans import RegisterOfTartans

def main():
    if len(sys.argv) < 2:
        return

    source = sys.argv[1].lower()
    args = sys.argv[2:]
    if len(args) == 0:
        args += ['grab', 'parse']
    args = map(lambda v: re.sub('_', '-', v).lower(), args)

    source = {
        'weddslist': Weddslist,
        'house-of-tartan': HouseOfTartan,
        'tartans-authority': TartansAuthority,
        'tartans-of-scotland': TartansOfScotland,
        'register-of-tartans': RegisterOfTartans,
    }.get(source, None)
    if source is None:
        exit()
    source = source()

    if 'grab' in args:
        source.grab()
    if 'parse' in args:
        source.parse()
    if 'update' in args:
        source.update_datapackage()


if __name__ == '__main__':
    main()
