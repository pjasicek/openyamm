#!/bin/bash
# Rebuild Starport Reach and the Hesper stage: the map, its minimap, D0 (whose surface door leads here), the stage.
set -e
cd "$(dirname "$0")/../../.."
python3 level_generation/projects/hesper_out1/build_out1.py
python3 level_generation/projects/hesper_out1/make_spawns_scenario.py   # hostile_spawns.yml's indices from this build
blender --background --factory-startup --python level_generation/projects/hesper_out1/build_minimap_blender.py \
    > level_generation/projects/hesper_out1/work/minimap_render.log 2>&1
python3 level_generation/projects/hesper_out1/finish_minimap.py
python3 level_generation/projects/hesper_d00/build_d00.py
python3 level_generation/projects/hesper_stage/stage.py
