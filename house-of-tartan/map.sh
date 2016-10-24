#!/usr/bin/env bash

(
  echo "\"Source\", \"Source ID\", \"Category\", \"Name\", \"Threadcount\" ";
  tail -n +2 raw.csv | \

  sed -r "s:^([0-9]+),\s*\"([^\"]*)\",\s*(P|R),\s*\"([^\"]*)\",\s*\"([^\"]*)\"$:\1|\2|\3|\4|\5:" |
  (
    prevIFS=$IFS
    IFS="|"
    while read id name flag palette sett
    do
      if [ "${flag}" == "P" ]
      then
        sett=`echo "${sett}" | sed -r "s|^\s*([a-zA-Z]*)([\sa-zA-Z0-9]+[a-zA-Z])([0-9]+)\s*$|\1/\2/\3|"`;
      fi
      source="House of Tartan";
      category=`echo ${name} | sed -r "s|^.+\s+([a-zA-Z/]+)\s+Tartan$|\1|"`;
      name=`echo ${name} | sed -r "s|^(.+)\s+[a-zA-Z/]+\s+Tartan$|\1|"`;
      echo "\"${source}\", \"${id}\", \"${category}\", \"${name}\", \"${palette} ${sett}\"";
    done
    IFS=$prevIFS
  )
) > mapped.csv

echo "Done.";
exit 0;