#!/bin/bash
# Refresh the scratch root's real copies (xeen data_tables, events/common) from assets_dev; add X8's map_stats row when
# assets_dev has none yet (a copy of XD-27's with X8's id, name, stem, music 25 and PLAINS).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
cd "$OYR"/output/studio_cal/x8
rm -rf root/worlds/xeen/data_tables root/worlds/xeen/events/common
cp -r ../../../assets_dev/worlds/xeen/data_tables root/worlds/xeen/
cp -r ../../../assets_dev/worlds/xeen/events/common root/worlds/xeen/events/
grep -q "	xeen_x8.blv	" root/worlds/xeen/data_tables/map_stats.txt || python3 - <<'PY'
p='root/worlds/xeen/data_tables/map_stats.txt'
lines=open(p).read().rstrip('\n').split('\n')
row=[l for l in lines if '\txeen_xd27.blv\t' in l][0].split('\t')
row[0]='9106';row[1]='Cloudreach';row[2]='xeen_x8.blv';row[5]='3';row[28]='25';row[29]='PLAINS'
open(p,'a').write('\n'.join([])+'\t'.join(row)+'\n')
print('added', '\t'.join(row))
PY
