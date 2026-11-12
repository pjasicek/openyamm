#!/usr/bin/env bash
# From the paid paints (project folder): compose -> rig + clips -> runtime -> viewer GLBs + manifest. Usage: scripts/rebuild.sh <viewer rev> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G=$here/../claude_shared/gltf_venv/bin/python
$G -W ignore scripts/compose.py 2>&1 | grep -E "Traceback|Error|FACEFIX|SEAM|TIERS|COMPOSED|MOUTH|HAIR|BODICE|NECK|SKIRT|LEGS"
MESH=work/uv_tex.npz scripts/rig.sh
scripts/build_runtime.sh ${2:-} 2>&1 | grep -E "LOD triangles|WINDING|Error|Traceback|install|INSTALL|export/"
$G -W ignore scripts/viewer.py export/mm6_pfem.glb rebuild > /dev/null
$G -W ignore scripts/viewer_manifest.py rebuild $1 | tail -1
