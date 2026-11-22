#!/bin/bash
# A read-only view of xeen_root with X2's built map and its map_stats row, for tools that take an asset root and no
# mount (town_feel.py): symlinks to xeen_root everywhere except the files X2 changes, which are copies.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -e
cd "$OYR"
X=$PWD/output/studio_play/xeen_root
C=$PWD/output/studio_cal/x2
R=$C/tf_root
mkdir -p $R/engine/data_tables $R/worlds/mm7/maps
for e in $X/*; do n=$(basename $e); [ "$n" = engine ] || [ "$n" = worlds ] || ln -sfn $e $R/$n; done
for e in $X/engine/*; do n=$(basename $e); [ "$n" = data_tables ] || ln -sfn $e $R/engine/$n; done
for e in $X/engine/data_tables/*; do n=$(basename $e); [ "$n" = map_stats.txt ] || ln -sfn $e $R/engine/data_tables/$n; done
for e in $X/worlds/*; do n=$(basename $e); [ "$n" = mm7 ] || ln -sfn $e $R/worlds/$n; done
for e in $X/worlds/mm7/*; do n=$(basename $e); [ "$n" = maps ] || [ "$n" = events ] || ln -sfn $e $R/worlds/mm7/$n; done
[ -L $R/worlds/mm7/events ] && { echo "tf_root: events is a link; remove it first"; exit 1; }
mkdir -p $R/worlds/mm7/events/maps
for e in $X/worlds/mm7/events/*; do n=$(basename $e); [ "$n" = maps ] || ln -sfn $e $R/worlds/mm7/events/$n; done
for e in $X/worlds/mm7/events/maps/*; do n=$(basename $e); case $n in xeen_x1.lua|xeen_x2.lua) ;; *) ln -sfn $e $R/worlds/mm7/events/maps/$n;; esac; done
cp --remove-destination $C/mount/worlds/mm7/events/maps/xeen_x1.lua $C/mount/worlds/mm7/events/maps/xeen_x2.lua $R/worlds/mm7/events/maps/
for e in $X/worlds/mm7/maps/*; do n=$(basename $e); case $n in xeen_x1.*|xeen_x2.*) ;; *) ln -sfn $e $R/worlds/mm7/maps/$n;; esac; done
for f in map_stats.txt; do cp --remove-destination $C/mount/engine/data_tables/$f $R/engine/data_tables/$f; done
for f in $C/mount/worlds/mm7/maps/xeen_x2.* $C/mount/worlds/mm7/maps/xeen_x1.*; do cp --remove-destination $f $R/worlds/mm7/maps/; done
