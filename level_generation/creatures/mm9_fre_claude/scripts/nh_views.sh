#!/bin/bash
# Pass 7: clay sheets of a head npz with r72's dress top (repo root). Usage: scripts/nh_views.sh <head npz> <out name> [colour c|''] [parts]
P=level_generation/creatures/mm9_fre_claude; cd $P
python3 scripts/nh_cmp_npz.py $1 work/nh/_v.npz 0 ${4:-dress} || exit 1
cd ../../..
for spec in "0,-0.01,0.68 0.40 front:right:back:q34:below:q34b" "0,-0.03,0.58 0.20 front:right:back:below"; do
  set -- $spec; Z=$( [ "$2" = 0.20 ] && echo neck || echo head )
  systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python $P/scripts/view_npz.py -- $P/work/nh/_v.npz $PWD/$P/review/newhead/_v_$Z $1 $2 600 $3 ${COL:-c} > /dev/null 2>&1
done
