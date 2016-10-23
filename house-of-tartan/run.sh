#!/usr/bin/env bash
echo 'House of tartans';

(
  wget -O- http://www.house-of-tartan.scotland.net/house/a.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/b.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/c.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/d.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/e.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/f.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/g.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/h.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/i.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/j.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/k.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/l.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/m.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/n.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/o.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/p.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/q.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/r.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/s.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/t.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/u.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/v.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/w.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/x.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/y.asp;
  wget -O- http://www.house-of-tartan.scotland.net/house/z.asp;
) \
| grep -oP "<a\s+href=\"alpha.htm\"\s+onClick=\"Frm\('\d+'\)\">.+?<\/a>" \
| sed -r "s|.*Frm.{2}([0-9]+).*>.*|\1|" \
| (
  while read id
  do
    url=`echo ${id} | sed -r "s|([0-9]+).*|http://www.house-of-tartan.scotland.net/house/TartanViewjs.asp?colr=Def\&tnam=\1|"`;
    html=`wget -O- ${url}`;
    name=`echo ${html} | grep -oP "class=\"title\">.*?</div>" | sed -r "s|.*>(.*?)<.*|\1|"`;
    sett=`echo ${html} | grep -oP "Tartan\.setup\(.+?\);" | sed -r "s|Tartan\.setup\((\".*?\"),\s*(\".*?\"),\s*\"(.*?)\"\);|\3, \2, \1|"`;
    echo "${id}, \"${name}\", ${sett}";
  done
) > data.csv

echo "Done.";

exit 0;
