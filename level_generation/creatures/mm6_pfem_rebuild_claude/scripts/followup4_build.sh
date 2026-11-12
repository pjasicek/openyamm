#!/usr/bin/env bash
# Follow-up 4 build: face_fix.py on the claimed GLB -> head LODs from tools/build_actor_lods.py -> splice (body LODs kept) -> shadow
# shrink -> winding fix -> winding check. Output work/followup4/cand_final.glb. Usage: scripts/followup4_build.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; repo="$(cd -- "$here/../../.." && pwd)"
G=$here/../claude_shared/gltf_venv/bin/python; W=work/followup4
python3 scripts/face_fix.py work/before_followup4/mm6_pfem.glb $W/cand.glb | tail -1
python3 scripts/lod_source.py $W/cand.glb $W/cand_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 --python "$repo/tools/build_actor_lods.py" -- \
  "$here/$W/cand_lod0.glb" "$here/$W/cand_lods.glb" --mesh-node PeasantF1 --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
$G -W ignore scripts/splice_head_lods.py $W/cand.glb $W/cand_lods.glb $W/cand_s.glb
$G -W ignore scripts/shrink_shadow_lods.py $W/cand_s.glb $W/cand_sh.glb PeasantF1
$G -W ignore scripts/fix_winding.py $W/cand_sh.glb $W/cand_final.glb | tail -1
$G -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $W/cand_final.glb | tail -1
