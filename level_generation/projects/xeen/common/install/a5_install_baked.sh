#!/bin/bash
# Lane A5 (2026-11-20, sixth session): install a built map WITH its lighting bake, so assets_dev never holds a map
# newer than its bake (the game refuses such a map: "cooked for different geometry", and other lanes' runs fail).
#   level_generation/projects/xeen/common/install/a5_install_baked.sh <stem> <project L4> <build dir> <bake profile> [--sources DIR]
# 1. a hard-link stage of assets_dev (cp -al; the map's own files unlinked first, so nothing is written through a
#    shared inode); 2. `oymap install` into the stage; 3. the bake from the stage (`bake_outdoor.py --assets`), under
#    locks/blender.lock; 4. the map's files and the bake copied into assets_dev by new file + rename, back to back;
#    5. terrain_swap.sh for the terrain weights; 6. stale_bakes.py. Remove the stage afterwards by its literal path
#    (printed at the end; hard links only, but 84k inodes).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/../../../../.."
stem=$1; project=$2; build=$3; profile=$4; shift 4
# the stage has no assets_source sibling: the bake always reads the repository's, plus an optional extra root
sources=(--sources "$PWD/assets_source")
if [[ ${1:-} == --sources ]]; then sources+=(--sources "$2"); fi
here=output/studio_cal/a5   # work output (stage, bake) stays in the lane folder
O=openyamm-studio/build-xeen/oymap
stage=$here/stage_${stem}_$$
mkdir -p $stage
cp -al assets_dev $stage/assets_dev
S=$stage/assets_dev
for f in maps/$stem.odm maps/$stem.scene.yml maps/$stem.studio.yml maps/$stem.lighting maps/$stem.bake.json \
         events/maps/$stem.lua; do
    rm -f "$S/worlds/xeen/$f"
done
tools/heavy.sh 8 $O install "$project" --build "$build" --root "$S"
# the bake profile names the map; point it at the stage
work=$here/bake_${stem}_$(date +%H%M%S)
mkdir -p "$work"
tools/heavy.sh 16 flock $here/locks/blender.lock blender --background --factory-startup --python-exit-code 1 \
    --python tools/lighting/bake_outdoor.py -- --profile "$profile" --output "$work" --assets "$S" "${sources[@]}" \
    > "$work/blender.log" 2>&1
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
echo "installed with its bake at $(date +%T): $stem"
bash level_generation/projects/xeen/common/install/terrain_swap.sh $stem
python3 tools/lighting/stale_bakes.py | tail -1
echo "stage left for a literal-path removal: $stage"
