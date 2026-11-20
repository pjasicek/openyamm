#!/usr/bin/env bash
# Head retexture chain after the Meshy job (README "Head retexture"): shade bake, eye domes, compose, runtime build,
# atlas head half, eye sockets, viewer GLBs and close renders -> export/mm6_gst.glb. head_uv.py ran before the job;
# rerunning it changes the upload and needs a new Meshy job.
set -euo pipefail
cd "$(dirname "$0")/.."
blender -b -P scripts/bake_head_shade.py 2>&1 | grep SHADE
blender -b -P scripts/add_eyes.py 2>&1 | grep EYE
python3 scripts/compose_head.py
scripts/build_pick.sh r55 eyes
python3 scripts/head_atlas.py export/mm6_gst_eyesr55.glb export/mm6_gst_eyesr55.glb
python3 scripts/eye_sockets.py export/mm6_gst_eyesr55.glb
cp export/mm6_gst_eyesr55.glb export/mm6_gst.glb
python3 scripts/viewer_variants.py export/mm6_gst.glb eyesr55 > /dev/null
REA_FACING=-Y blender -b -P scripts/close_views.py -- review/viewer/mm6_gst_a_eyesr55.glb eyesr55 > work/close_eyesr55.log 2>&1
