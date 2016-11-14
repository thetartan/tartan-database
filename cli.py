import sys
import re
from src.sources.weddslist import Weddslist
from src.sources.house_of_tartan import HouseOfTartan
from src.sources.tartans_authority import TartansAuthority

def main():
    if len(sys.argv) < 2:
        return

    source = sys.argv[1].lower()
    args = sys.argv[2:]
    if len(args) == 0:
        args += ['grab', 'parse']
    args = map(lambda v: re.sub('_', '-', v).lower(), args)

    if source == 'weddslist':
        source = Weddslist()
    elif source == 'house-of-tartan':
        source = HouseOfTartan()
    elif source == 'tartans-authority':
        source = TartansAuthority()
    else:
        exit()

    if 'grab' in args:
        print source, 'grab'
        source.grab()
    if 'parse' in args:
        print source, 'parse'
        source.parse()


if __name__ == '__main__':
    main()
