#!/usr/bin/env bash
# Rebuild the New Sorpigal props (and the later Silver Cove / Misty Islands / Ironfist / Eel and outd2 props) from scratch: textures -> scan rocks (../scripts/build_prop.py with rocks.json) ->
# models -> review sheets -> finish (link LODs, validate) [--install copies them to assets_dev/worlds/mm6/models].
# Usage: build.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
cd "$here"
python3 scripts/make_textures.py
python3 scripts/make_water_textures.py
# fire props (2026-10-09 rework): CC0 Poly Haven sets -> props/textures_pbr/ (downloads only what is missing)
python3 -I scripts/fetch_pbr.py > /dev/null
python3 -I scripts/make_pbr_textures.py > /dev/null
mkdir -p work/logs
for rock in swordboulder surfrock_a surfrock_b; do
  mkdir -p "$rock"
  PROPS_JSON="$here/rocks.json" PROP_ROOT="$here/$rock" \
    "$blender" --background --python ../scripts/build_prop.py -- "$rock" > "work/logs/$rock.log" 2>&1 &
done
wait
"$blender" --background --python scripts/build_cauldron.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_fountain.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_swordstone.py 2>&1 | grep -E "SWORDSTONE|LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_surfrock.py -- surfrock_a SurfRockA 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_surfrock.py -- surfrock_b SurfRockB 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_buoy.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_flag.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_flag.py -- flag1 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_campfire.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_burningrock.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_logfire.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_skullpile.py 2>&1 | grep -E "LEVEL|Error|Traceback"
# outd2 (2026-10-09): pedestal, food bowl, keg and the impaled corpses (posed MM6 peasants, read only)
"$blender" --background --python scripts/build_pedestal.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_foodbowl.py 2>&1 | grep -E "LEVEL|Error|Traceback"
"$blender" --background --python scripts/build_keg.py 2>&1 | grep -E "LEVEL|Error|Traceback"
for corpse in corpse04 corpse05 corpse06 corpse16; do
  "$blender" --background --python scripts/build_corpse.py -- "$corpse" 2>&1 | grep -E "LEVEL|STUMPS|Error|Traceback"
done
for pair in cauldron:ckfyr00 fountain:fount1 swordstone:swrdstn swordstone_empty:swrdstx surfrock_a:searka01 \
            surfrock_b:searkb01 buoy:bouy0 flag:fla3__01 flag1:fla1__01 campfire:cmpfyr00 burningrock:brnrock0 \
            logfire:dec04a skullpile:sklplrev pedestal:ped06 foodbowl:foodbowl keg:smlbarel corpse04:corpse04 corpse05:corpse05 \
            corpse06:corpse06 corpse16:corpse16; do
  prop=${pair%%:*}; sprite=${pair##*:}
  "$blender" --background --python scripts/review.py -- "$prop" "work/${prop}_export.glb" 0 2>&1 | grep -E "Error|Traceback" || true
  python3 scripts/sheet.py "$prop" "$sprite" > /dev/null
  python3 scripts/finish.py "$prop" "$@"
done
