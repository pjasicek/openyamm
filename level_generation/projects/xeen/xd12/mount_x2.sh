#!/bin/bash
# A scratch mount with this map and X2's current build (output/studio_cal/x2/mount), so the tower door and the falls
# can be walked through to X2. X2's files are copied over, never changed; this map's files are copied on top.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
R=$OYR
X=$R/output/studio_cal/xd12
X2=$R/output/studio_cal/x2/mount
M=$X/mount_x2
mkdir -p $M
cp -r $X2/. $M/
cp -r $X/mount/worlds/. $M/worlds/
grep -v -P "^9140\t" $X2/engine/data_tables/map_stats.txt > $M/engine/data_tables/map_stats.txt
grep -P "^9140\t" $X/mount/engine/data_tables/map_stats.txt >> $M/engine/data_tables/map_stats.txt
grep -c "" $M/engine/data_tables/map_stats.txt
grep -v -P "^9140\t" $X2/engine/data_tables/bolster_maps.txt > $M/engine/data_tables/bolster_maps.txt
grep -P "^9140\t" $X/mount/engine/data_tables/bolster_maps.txt >> $M/engine/data_tables/bolster_maps.txt
