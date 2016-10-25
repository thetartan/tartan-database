#!/usr/bin/env bash

(
  cat house-of-tartan/mapped.csv
  tail -n +2 weddslist/mapped.csv
) > data.csv

# Update resource size
size=`stat --printf="%s" data.csv`;
package=`cat datapackage.json | sed -r "s|^(\s*\"bytes\":)\s*[0-9]+\s*$|\1 ${size}|"`;
echo "${package}" > datapackage.json

echo "Done.";
exit 0;
