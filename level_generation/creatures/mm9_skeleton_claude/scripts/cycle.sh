#!/usr/bin/env bash
# rebuild -> runtime -> viewer tiers + manifest. Usage: scripts/cycle.sh <revision> [--install]
set -euo pipefail
cd "$(dirname "$0")/.."; G=../claude_shared/gltf_venv/bin/python; rev=$1; shift
TOKEN=97b36ea68c87470ba34e79692ae66ac0 scripts/rebuild.sh uv_final.blend 2>&1 | grep -E 'FAILED|Traceback|ARMCLEAR|body %|head %|TONE' | cut -c1-160
scripts/build_runtime.sh "$@" 2>&1 | grep -E 'LOD triangles|Dead:|WINDING|INVERTED|Error' | cut -c1-200
$G scripts/viewer_tiers.py 2>&1 | tail -1
$G scripts/make_viewer_manifest.py $rev skel_a="Skeleton, Bone Thrasher (SKELETON2)"=review/viewer/skel_a.glb skel_r="Skeletoid, Skull Thrower (SKELETONRED)"=review/viewer/skel_r.glb 2>&1 | tail -1 | cut -c1-40
