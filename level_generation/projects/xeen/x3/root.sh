#!/bin/bash
# A5 (2026-11-20, fifth session): a read-only view of assets_dev for X3's walk, hostility run and town_feel until A2
# writes X3's rows: symlinks to assets_dev everywhere except
#   worlds/xeen/data_tables/map_stats.txt, outdoor_travels.txt (X3's row and travel added: new files), and
#   engine/data_tables/house_data.txt, map_stats.txt, monster_data.txt (only under tf/: town_feel reads the engine's
#   tables; there the world's rows are appended to them).
# Usage: root.sh [game|tf]  (both by default; remove an old one first)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
A=$PWD/assets_dev
C=$PWD/output/studio_cal/x3
X3ROW=$'9101\tLifeforce Lagoon\txeen_x3.odm\t0\t0\t2\t672\t0\t0\t2\t1\t2\t10\t40\t20\t40\tXeen Swamp Thing\tXeen Swamp Thing\t1\t 2-3\tXeen Toad\tXeen Toad\t1\t 2-4\tXeen Zombie\tXeen Zombie\t1\t 2-3\t48\tPLAINS\tmap_studio\t0\t0\t-\t'
X4ROW=$'9102\tBurlock Savannah\txeen_x4.odm\t0\t0\t2\t672\t7\t3\t2\t1\t2\t10\t27\t33\t40\tXeen Renegade\tXeen Renegade\t1\t 2-3\tXeen Ogre\tXeen Ogre\t0\t 2-3\tXeen Gargoyle\tXeen Gargoyle\t1\t 2-4\t29\tPLAINS\tmap_studio\t0\t0\t-\t'
X3TRAVEL=$'xeen_x3.odm\t\t\t\t\t\t\txeen_x5.odm\tleft\t5\txeen_x2.odm\tright\t5\t\tLifeforce Lagoon\t\t\t\t\t'
# The game reads no symlinked file (world.yml "could not read"): its root is a hard-link copy whose two changed
# tables are new files (unlinked first, so assets_dev's inodes are never written).
what=${1:-both}
if [ "$what" != tf ]; then
if [ -e $C/root ]; then echo "$C/root exists: remove it first"; exit 1; fi
cp -al $A $C/root
python3 - "$C/root/worlds/xeen/data_tables" "$X3ROW"$'\n'"$X4ROW" "$X3TRAVEL" <<'PY'
import os, sys
d, row, travel = sys.argv[1:4]
for name, extra in (('map_stats.txt', row), ('outdoor_travels.txt', travel)):
    path = os.path.join(d, name)
    text = open(path, encoding='latin-1').read()
    os.remove(path)
    with open(path, 'w', encoding='latin-1') as f:
        f.write(text + extra + '\n')
PY
fi
[ "$what" = game ] && exit 0
for R in $C/tf; do
    if [ -e "$R" ]; then echo "$R exists: remove it first (ls, then rm -r with its literal path)"; exit 1; fi
    mkdir -p $R/worlds/xeen/data_tables $R/engine/data_tables
    for e in $A/*; do n=$(basename $e); [ "$n" = engine ] || [ "$n" = worlds ] || ln -s $e $R/$n; done
    for e in $A/worlds/*; do n=$(basename $e); [ "$n" = xeen ] || ln -s $e $R/worlds/$n; done
    for e in $A/worlds/xeen/*; do n=$(basename $e); [ "$n" = data_tables ] || ln -s $e $R/worlds/xeen/$n; done
    for e in $A/worlds/xeen/data_tables/*; do
        n=$(basename $e); case $n in map_stats.txt|outdoor_travels.txt) ;; *) ln -s $e $R/worlds/xeen/data_tables/$n;; esac
    done
    { cat $A/worlds/xeen/data_tables/map_stats.txt; printf '%s\n' "$X3ROW"; } > $R/worlds/xeen/data_tables/map_stats.txt
    { cat $A/worlds/xeen/data_tables/outdoor_travels.txt; printf '%s\n' "$X3TRAVEL"; } \
        > $R/worlds/xeen/data_tables/outdoor_travels.txt
    for e in $A/engine/*; do n=$(basename $e); [ "$n" = data_tables ] || ln -s $e $R/engine/$n; done
    for e in $A/engine/data_tables/*; do
        n=$(basename $e)
        if [ "$R" = "$C/tf" ]; then case $n in house_data.txt|map_stats.txt|monster_data.txt) continue;; esac; fi
        ln -s $e $R/engine/data_tables/$n
    done
done
# town_feel's root: the engine's tables with the world's rows after them (the world's data rows only)
for n in house_data.txt monster_data.txt; do
    { cat $A/engine/data_tables/$n; awk -F'\t' '$1 ~ /^[0-9]+$/' $A/worlds/xeen/data_tables/$n; } > $C/tf/engine/data_tables/$n
done
{ cat $A/engine/data_tables/map_stats.txt; awk -F'\t' '$1 ~ /^[0-9]+$/' $C/tf/worlds/xeen/data_tables/map_stats.txt; } \
    > $C/tf/engine/data_tables/map_stats.txt
echo "roots: $C/root (game), $C/tf (town_feel)"
