#!/bin/bash
# Bake a Hesper outdoor map's lighting from the stage (tools/lighting/bake_outdoor.py with the stage as its asset
# root) into output/hesper_stage/bakes, then re-run stage.py, which installs a bake only while its map is unchanged.
#   level_generation/projects/hesper_stage/bake.sh [project] [samples]     (default: hesper_out1, the profile's)
set -e
cd "$(dirname "$0")/../../.."
project=${1:-hesper_out1}
profile=level_generation/projects/$project/bake_profile.json
stage=output/hesper_stage
work=$stage/bake_work/$project
rm -rf "$work"
mkdir -p "$work" "$stage/bakes"
blender --background --factory-startup --python-exit-code 1 --python tools/lighting/bake_outdoor.py -- \
    --profile "$profile" --output "$work" --assets "$stage/assets_editor_dev" \
    --sources assets_source --sources "$stage/sources" ${2:+--samples $2} > "$work/blender.log" 2>&1
map=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['map'])" "$profile")
cp "$work/${map%.odm}.lighting" "$work/${map%.odm}.bake.json" "$stage/bakes/"
python3 level_generation/projects/hesper_stage/stage.py
