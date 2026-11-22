#!/bin/bash
# Lane A7 (eighth session): install built dungeons WITH their lighting bake, so assets_dev never holds a map newer than
# its bake. For each key: the map is already built and installed into the scratch root (xcycle.sh); bake it from that
# root (one Blender at a time in the lane, output/studio_cal/a7_bake.lock), then copy the map's four files and the
# bake into assets_dev by new file + rename, back to back. Usage: install_baked.sh <root> <key>...
set -u
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../.." && pwd)"; A=$R/output/studio_cal/a7; cd $R   # A: the lane folder, for the bake logs
ROOT=$1; shift
D=$R/assets_dev/worlds/xeen
for k in "$@"; do
  S=$ROOT/worlds/xeen
  flock $R/output/studio_cal/a7_bake.lock bash $R/level_generation/projects/xeen/common/bake/a7_bake_map.sh $k $ROOT --sources $R/assets_source > $A/s8_bake_$k.log 2>&1 \
    || { echo "bake $k failed"; tail -3 $A/s8_bake_$k.log; continue; }
  B=$R/output/studio_cal/$k/a7_bake/bake
  files=(maps/xeen_$k.blv maps/xeen_$k.scene.yml maps/xeen_$k.studio.yml events/maps/xeen_$k.lua)
  for f in "${files[@]}"; do cp "$S/$f" "$D/$f.a7new" && chmod 0644 "$D/$f.a7new"; done
  for f in xeen_$k.lighting xeen_$k.bake.json; do cp "$B/$f" "$D/maps/$f.a7new" && chmod 0644 "$D/maps/$f.a7new"; done
  for f in "${files[@]}" maps/xeen_$k.lighting maps/xeen_$k.bake.json; do mv -f "$D/$f.a7new" "$D/$f"; done
  echo "installed with its bake at $(date +%T): $k"
done
python3 tools/lighting/stale_bakes.py | tail -1
