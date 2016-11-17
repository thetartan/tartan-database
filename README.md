# Tartan threadcounts from different sources

## Sources

- Weddslist (http://www.weddslist.com/tartans/links.html) - 
data in [data/weddslist](data/weddslist) folder.
- House of Tartan (http://www.house-of-tartan.scotland.net/) - 
data in [data/house-of-tartan](data/house-of-tartan) folder.
- Scottish Tartans Authority (http://www.tartansauthority.com/) -
data in [data/tartans-authority](data/tartans-authority) folder.
- Scottish Register of Tartans (https://www.tartanregister.gov.uk/) -
data in [data/register-of-tartans](data/register-of-tartans) folder.
- Tartans of Scotland (http://www.tartans.scotland.net/) (without threadcounts) -
data in [data/tartans-of-scotland](data/tartans-of-scotland) folder.

Dataset files are available in the `data` directory - each dataset in its
own subfolder. Raw/unparsed data can be found in `storage` directory after 
running any of processing scripts.

## Requirements

- Python 2.7;
- `requests` library (version 2.9.1 properly works with TLSv1; 
newer versions are somehow broken);
- `Pillow` library (for Scottish Tartans Authority).

## Usage

Run corresponding bash script to update a source:

- `./all` - all sources
- `./weddslist` - for Weddslist
- `./house-of-tartan` - for House of Tartan
- `./tartans-authority` - for Scottish Tartans Authority
- `./tartans-of-scotland` - for Tartans os Scotland
- `./register-of-tartans` - for Scottish Register of Tartans

Type `./<source> --help` to list possible arguments 
(*note:* `./all --help` will display arguments multiple times - choose any,
they are completely the same).

## Configuration

Set this environment variables before running bash scripts:

- `DATASET_AUTHOR` - to update `author` field in `datapackage.json`
- `DATASET_VERSION` - to update `version` field in `datapackage.json`

## About cache

Grabbers by their nature are very fragile scripts. Depending on situation,
it may be possible that they have the only chance to run. So it's good idea
to split parsing into two steps: grabbing necessary files to local hard drive,
and then process them. Having local cache, parser may run as many times as it 
needs; it should not wait for grabbing files. This project uses `storage`
folder to store grabbed files - each source has own subfolder.

Meantime, it's bad idea to store all grabbed files in GIT; much better is to 
compress them and store archive - since grabbed data is usually very similar
(at least, page header and footer will be the same for single site), it will
reduce data size 10 and more times.

To save raw grabbed files after running grabbers, you can use `stg` script:
`./stg pack` - pack `storage` folder, `./stg unpack` - restore previously 
packed files.
