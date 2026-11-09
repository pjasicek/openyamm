#!/usr/bin/env bash
# The post-LOD steps of build_runtime_sc.sh from work/mm9_scholar_rv.glb (texture-only changes: head/tier images), no Blender. Project folder.
# scripts/tail_sc.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_scholar; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; export PYTHONPATH=/usr/lib/python3/dist-packages
"$G" -W ignore scripts/tier_images.py work/${n}_rv.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb 2>&1 | tail -1
"$G" -W ignore scripts/legs_hide.py export/${n}_skins2.glb export/${n}_legs.glb ${LEGSHIDE:-Death:0.05:0.35:0.05:0.3:0.3:0.42 Dead:0:0:0.05:0.3} 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_legs.glb export/${n}_floor.glb $(cat scripts/floor_ops_sc.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_floor.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -2; fi
ls -la export/${n}.glb
