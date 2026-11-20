#!/bin/bash
# Rebuild the Scour: the map, its minimap, then the stage (under its lock). The dungeons whose exits lead here (D3, D4,
# D8) and the Undervault (its tunnel) read out2_build.json: rebuild them after the Scour's arrivals change
# (level_generation/projects/hesper_stage/rebuild_all.sh does both).
set -e
cd "$(dirname "$0")/../../.."
# Builds hold the stage lock shared (BUILDER_GUIDE "Locks"): stage.py waits until no build is mid-write.
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out2/build_out2.py
flock -s output/hesper_stage/locks/stage.lock \
    blender --background --factory-startup --python level_generation/projects/hesper_out2/build_minimap_blender.py \
    > level_generation/projects/hesper_out2/work/minimap_render.log 2>&1
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out2/finish_minimap.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py > /dev/null
