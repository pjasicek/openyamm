#!/bin/bash
# A7 lighting bake of one Xeen dungeon by key: a7_bake_map.sh <key> <asset root> [extra bake_indoor args]; output in
# output/studio_cal/<key>/a7_bake/bake; install with ../install/install_bake.py <key>. Take
# output/xeen_locks/bake.lock around it (one bake at a time in the program).
set -e
k=$1; root=$2; shift 2
cd "$(dirname "$(readlink -f "$0")")/../../../../.."
out=output/studio_cal/$k/a7_bake/bake
mkdir -p $out
tools/heavy.sh 16 \
  blender --background --factory-startup --python-exit-code 1 --python tools/lighting/bake_indoor.py -- \
  --profile tools/lighting/baked_indoors/profiles/xeen_$k.yml --output $out --assets $root \
  --game-binary "$PWD/build-xeen/game/openyamm" "$@"
