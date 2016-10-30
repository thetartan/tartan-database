#!/usr/bin/env bash

echo "Parse data..."
/usr/bin/env python house-of-tartan.py > house-of-tartan.csv
/usr/bin/env python weddslist.py > weddslist.csv

echo "Merge database files..."
(
  cat house-of-tartan.csv
  tail -n +2 weddslist.csv
) > database.csv

echo "Updating datapackage.json file..."
package=`cat datapackage.json | python datapackage.py`
echo "${package}" > datapackage.json

echo "Finished.";
exit 0;
