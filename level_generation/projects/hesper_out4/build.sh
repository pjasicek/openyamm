#!/bin/bash
# Rebuild the Crown and stage it: the sky layers, the map, its minimap, the stage (under the stage lock). Re-bake the
# lighting after every map build (README, Bake).
set -e
cd "$(dirname "$0")/../../.."
python3 level_generation/projects/hesper_out4/make_sky_out4.py
mkdir -p output/hesper_stage/locks
# The build rewrites source/ and runtime/: under the stage lock, shared (builds run in parallel; stage.py waits).
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out4/build_out4.py
blender --background --factory-startup --python level_generation/projects/hesper_out4/build_minimap_blender.py \
    > level_generation/projects/hesper_out4/work/minimap_render.log 2>&1
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out4/finish_minimap.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
