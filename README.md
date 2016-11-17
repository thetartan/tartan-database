# Tartan threadcounts from different sources

## Sources

- Weddslist (http://www.weddslist.com/tartans/links.html)
- House of Tartan (http://www.house-of-tartan.scotland.net/)
- Scottish Tartans Authority (http://www.tartansauthority.com/)
- Scottish Register of Tartans (https://www.tartanregister.gov.uk/)
- Tartans of Scotland (http://www.tartans.scotland.net/)

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

**Arguments:**

- `grab` - to download files that source needs to parse data, but do not parse them;
- `parse` - parse downloaded files (but do not download or update any of them);
- no arguments is equivalent to passing `grab parse` - full update of dataset.

**Example:**

`./weddslist grab parse` - download html files, parse them, update `datapackage.json`
and copy new `data.csv` and `datapackage.json` to `data/weddslist` folder.

## Configuration

Set this environment variables before running bash scripts:

- `DATASET_AUTHOR` - to update `author` field in `datapackage.json`
- `DATASET_VERSION` - to update `version` field in `datapackage.json`

## Other stuff

To save raw grabbed files after running grabbers, you can use `stg` script:
`./stg pack` - pack `storage` folder, `./stg unpack` - restore previously 
packed files. It may be useful when improving parsers - grabbing files may take
a while, so it's better to use cached ones.
