# Tartan threadcounts from different sources

## Sources

- Weddslist (http://www.weddslist.com/tartans/links.html)
- House of Tartan (http://www.house-of-tartan.scotland.net/)
- Scottish Tartans Authority (http://www.tartansauthority.com/)

Dataset files are available in the `data` directory - each dataset in its
own subfolder. Raw/unparsed data can be found in `storage` directory.

## Requirements

- Python 2.7
- `requests` library
- `Pillow` library (for Scottish Tartans Authority)

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
