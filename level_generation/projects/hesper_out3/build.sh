#!/bin/bash
# Rebuild the Brood Spires and stage it: the map, its scenarios' indices, its minimap, then the stage (under its lock).
# The lighting bake is separate (README, Build): re-bake after every map build.
set -e
cd "$(dirname "$0")/../../.."
mkdir -p output/hesper_stage/locks
# The build rewrites source/ and runtime/, which stage.py reads: shared stage lock (BUILDER_GUIDE, Locks).
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out3/build_out3.py
python3 level_generation/projects/hesper_out3/make_scenarios.py
blender --background --factory-startup --python level_generation/projects/hesper_out3/build_minimap_blender.py \
    > level_generation/projects/hesper_out3/work/minimap_render.log 2>&1
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out3/finish_minimap.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
