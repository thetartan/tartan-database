#!/usr/bin/env bash

(
  echo "\"Source\", \"Source ID\", \"Type\", \"Category\", \"Name\", \"Threadcount\" ";
  tail -n +2 raw.csv | sed -r "s|^.*$|\"Weddslist\", \"\", \"TDF\", &|"
) > mapped.csv

echo "Done.";
exit 0;