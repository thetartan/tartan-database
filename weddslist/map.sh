#!/usr/bin/env bash

(
  echo "\"Source\", \"Source ID\", \"Category\", \"Name\", \"Threadcount\" ";
  tail -n +2 raw.csv | sed -r "s|^.*$|\"Weddslist\", \"\", &|"
) > mapped.csv

echo "Done.";
exit 0;