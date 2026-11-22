#!/bin/bash
# Rebase (A5, 2026-11-20): a hard-link play root of today's assets_dev plus the Xeen stand-in maps of
# output/studio_play/xeen_root (maps, events, terrain materials, the XD textures and sounds, their table rows).
# The old xeen_root's engine tables are older than today's game (solo_shop_stock.yml), so it no longer loads.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -e
cd "$OYR"
R=${1:-output/studio_cal/x1/xroot}
OLD=output/studio_play/xeen_root
[ -e "$R" ] && { echo "$R exists"; exit 1; }
cp -al assets_dev "$R"
for d in maps events/maps terrain_materials; do
  for f in $OLD/worlds/mm7/$d/xeen_*; do ln "$f" "$R/worlds/mm7/$d/"; done
done
for f in $OLD/worlds/mm7/textures_x2/xn* $OLD/worlds/mm7/textures_x4/xn* $OLD/worlds/mm7/audio/xodrum*; do
  t="$R/${f#$OLD/}"; mkdir -p "$(dirname "$t")"; [ -e "$t" ] || ln "$f" "$t"
done
for t in map_stats outdoor_travels bolster_maps; do
  f=$R/engine/data_tables/$t.txt
  { cat "$f"; grep -P "xeen_|^91[34][0-9]\t" $OLD/engine/data_tables/$t.txt | grep -v -F -f <(cut -f1-3 "$f" | grep -P "xeen_" || true) || true; } > "$f.new"
  mv "$f.new" "$f"
done
grep -c xeen_ $R/engine/data_tables/map_stats.txt $R/engine/data_tables/outdoor_travels.txt $R/engine/data_tables/bolster_maps.txt
