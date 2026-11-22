#!/bin/bash
# play_mount.sh: a combined read-only test mount: X2's mount (copied, not linked) plus this dungeon's mount, with this
# map's map_stats row appended to X2's table, so the exit to X2 can be followed in a playtest.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -e
R=$OYR; X=$R/output/studio_cal/xd06; D=$X/play_mount
mkdir -p $D
cp -r $R/output/studio_cal/x2/mount/. $D/
cp -r $X/mount/worlds/. $D/worlds/
ROW=$(grep -P "^\d+\t[^\t]*\txeen_xd06\.blv\t" $X/mount/engine/data_tables/map_stats.txt)
grep -v -P "\txeen_xd06\.blv\t" $D/engine/data_tables/map_stats.txt > $D/engine/data_tables/map_stats.txt.new
printf '%s\n' "$ROW" >> $D/engine/data_tables/map_stats.txt.new
mv $D/engine/data_tables/map_stats.txt.new $D/engine/data_tables/map_stats.txt
# this map's bolster row (map_stats.bolster) appended to X2's bolster table, replacing any older copy of it
BROW=$(grep -P "^9139\t" $X/mount/engine/data_tables/bolster_maps.txt)
grep -v -P "^9139\t" $D/engine/data_tables/bolster_maps.txt > $D/engine/data_tables/bolster_maps.txt.new
printf '%s\n' "$BROW" >> $D/engine/data_tables/bolster_maps.txt.new
mv $D/engine/data_tables/bolster_maps.txt.new $D/engine/data_tables/bolster_maps.txt
grep -c "xeen_x2.odm\|xeen_xd06.blv" $D/engine/data_tables/map_stats.txt
