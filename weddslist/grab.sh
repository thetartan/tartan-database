#!/usr/bin/env bash

(
  echo "rb|Robert Bradford";
  echo "tinsel|Thomas Insel";
  echo "x|Jim McBeath & Joseph Shelby";
  echo "sts|Scottish Tartans Society";
  echo "misc|Miscellaneous";
) |
(
  echo "\"Category\", \"Name\", \"Threadcount\"";
  while read line
  do
    id=${line%%"|"*}
    group=${line#*"|"}
    (
      wget -O- http://www.weddslist.com/cgi-bin/tartans/pg.pl?source=${id} \
        | grep "<option value=" \
        | sed -r "s|<option value=\"(.*?)\">(.*)|\"\2\", \"\1\"|";
    ) \
    | (
      while read sett
      do
        sett=`echo ${sett} | sed -r "s|^([^\[]*)\[?(.*)$|\1\2|"`;
        echo "\"${group}\", ${sett}";
      done
    )
  done
) > raw.csv

echo "Done.";
exit 0;
