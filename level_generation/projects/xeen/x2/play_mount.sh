#!/bin/bash
# The play mount for X2's walk and pictures: X2's mount (X2 and the rebuilt X1) plus the dungeons the other agents have
# built so far (copied from their mounts, read only; their map_stats rows appended). Never written by anyone else.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -e
cd "$OYR"
C=output/studio_cal/x2
D=$C/play_mount
mkdir -p $D
cp -r $C/mount/. $D/
HAVE=""
for k in xd21 xd27 xd06 xd12; do
  S=output/studio_cal/$k/mount
  if [ -f $S/worlds/mm7/maps/xeen_$k.blv ]; then
    cp $S/worlds/mm7/maps/xeen_$k.* $D/worlds/mm7/maps/
    mkdir -p $D/worlds/mm7/events/maps
    [ -f $S/worlds/mm7/events/maps/xeen_$k.lua ] && cp $S/worlds/mm7/events/maps/xeen_$k.lua $D/worlds/mm7/events/maps/
    ROW=$(grep -P "^\d+\t[^\t]*\txeen_$k\.blv\t" $S/engine/data_tables/map_stats.txt || true)
    if [ -n "$ROW" ] && ! grep -q "xeen_$k.blv" $D/engine/data_tables/map_stats.txt; then
      printf '%s\n' "$ROW" >> $D/engine/data_tables/map_stats.txt
    fi
    HAVE="$HAVE $k"
  fi
done
echo $HAVE
