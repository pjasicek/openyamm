#!/bin/bash
# texsize.sh name...: logical size of each face texture (xeen, mm7, mm6, mm8 worlds)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
O=$OYR/openyamm-studio/build-xeen/oymap
for t in "$@"; do
  for w in xeen mm7 mm6 mm8; do
    r=$($O assets "$t" --assets $OYR/assets_dev --world $w --kind texture --limit 60 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for x in d['textures']:
    if x['name'].lower()=='$t'.lower(): print(x['name'], x.get('width'), x.get('height'), x.get('liquid',''))" | head -1)
    [ -n "$r" ] && { echo "$w $r"; break; }
  done
  [ -z "$r" ] && echo "MISSING $t"
done
