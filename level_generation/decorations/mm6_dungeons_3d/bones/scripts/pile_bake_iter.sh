#!/bin/sh
# Compose the baked pile's textures, rebuild its LODs and render the close-up compare: pile_bake_iter.sh <tag> <size>
cd "$(dirname "$0")"
python3 compose_pile.py pilebaked 2048 ${2:-2048} 0.85 1.0 ${CHROMA:-0.6} ${LIGHT:-0.8} | tail -1
/snap/bin/blender --background ../work/pile_low.blend --python build_pile_baked.py -- pilebaked 2>&1 | grep -E "Error|Trace"
./pile_cmp.sh $1
