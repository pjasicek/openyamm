#!/bin/bash
# Lane A6 (2026-11-20, eighth session): install a built map WITH its lighting bake, after A5's install_baked.sh, so
# assets_dev never holds a map newer than its bake.
#   level_generation/projects/xeen/common/install/a6_install_baked.sh <stem> <project L4> <build dir> <bake profile>
# 1. a hard-link stage of assets_dev (cp -al; the map's own files unlinked first); 2. `oymap install` into the stage;
# 3. the bake from the stage under output/studio_cal/a6_bake.lock (one Blender at a time in the lane); 4. the map's
# files and the bake into assets_dev by new file + rename, back to back; 5. A5's terrain_swap.sh (A5's terrain lock:
# the liquid edges are shared); 6. stale_bakes.py; 7. the stage removed (checked literal path).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/../../../../.."
stem=$1; project=$2; build=$3; profile=$4
here=output/studio_cal/a6
O=openyamm-studio/build-xeen/oymap
stage=$here/stage_${stem}_$$
mkdir -p $stage
cp -al assets_dev $stage/assets_dev
S=$stage/assets_dev
# A4's rule (2026-11-20): the world's data tables are copied, never hard-linked (oymap install writes rows into them)
python3 - "$S/worlds/xeen/data_tables" <<'PY2'
import os, shutil, sys
t = os.path.realpath(sys.argv[1])
assert '/output/studio_cal/a6/stage_' in t and t.endswith('/worlds/xeen/data_tables')
shutil.rmtree(t)
shutil.copytree('assets_dev/worlds/xeen/data_tables', t)
PY2
for f in maps/$stem.odm maps/$stem.scene.yml maps/$stem.studio.yml maps/$stem.lighting maps/$stem.bake.json \
         events/maps/$stem.lua; do
    rm -f "$S/worlds/xeen/$f"
done
tools/heavy.sh 8 $O install "$project" --build "$build" --root "$S"
work=$here/bake_${stem}_$(date +%H%M%S)
mkdir -p "$work"
tools/heavy.sh 16 flock output/xeen_locks/bake.lock blender --background --factory-startup --python-exit-code 1 \
    --python tools/lighting/bake_outdoor.py -- --profile "$profile" --output "$work" --assets "$S" \
    --sources "$PWD/assets_source" > "$work/blender.log" 2>&1
python3 - "$work/report.json" <<'PY'
import json, sys
deps = json.load(open(sys.argv[1]))['dependencies']
tables = [d for d in deps if 'terrain_tile_data' in d]
assert tables == ['engine/data_tables/terrain_tile_data_2.txt'], f'wrong tile table: {tables}'
PY
D=assets_dev/worlds/xeen
for f in maps/$stem.odm maps/$stem.scene.yml maps/$stem.studio.yml events/maps/$stem.lua; do
    cp "$S/worlds/xeen/$f" "$D/$f.new"; chmod 0644 "$D/$f.new"
done
for f in $stem.lighting $stem.bake.json; do
    cp "$work/$f" "$D/maps/$f.new"; chmod 0644 "$D/maps/$f.new"
done
for f in maps/$stem.odm maps/$stem.scene.yml maps/$stem.studio.yml events/maps/$stem.lua maps/$stem.lighting \
         maps/$stem.bake.json; do
    mv -f "$D/$f.new" "$D/$f"
done
echo "installed with its bake at $(date +%T): $stem (bake $work)"
bash level_generation/projects/xeen/common/install/terrain_swap.sh $stem
# stale_bakes exits non-zero when any map is stale (another lane's table change): report, never stop here
{ python3 tools/lighting/stale_bakes.py || true; } | tail -1
grep -n "$stem" assets_dev/STALE_LIGHTING_BAKES.txt && echo "$stem is listed stale" || echo "$stem not stale"
python3 - "$stage" <<'PY'
import os, shutil, sys
t = os.path.realpath(sys.argv[1])
assert os.path.basename(t).startswith('stage_') and t.startswith(os.path.realpath('output/studio_cal/a6') + '/')
shutil.rmtree(t)
print('stage removed:', t)
PY
