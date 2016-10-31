#!/usr/bin/env bash

echo "Parse data..."
/usr/bin/env python sources/house-of-tartan.py > data/house-of-tartan.csv
/usr/bin/env python sources/weddslist.py > data/weddslist.csv

echo "Merge database files..."
(
  cat data/house-of-tartan.csv
  tail -n +2 data/weddslist.csv
) > database.csv

echo "Updating datapackage.json file..."
package=`cat datapackage.json | python datapackage.py`
echo "${package}" > datapackage.json

echo "Finished.";
exit 0;
