#!/usr/bin/env bash

(
  cat house-of-tartan/mapped.csv
  tail -n +2 weddslist/mapped.csv
) > data.csv

echo "Done.";
exit 0;
