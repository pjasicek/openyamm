#!/usr/bin/env bash
# Runtime GLB from the gated animation master (work/anim_v4.blend; chain before it: build_rig -> retarget_mixamo ->
# author_clips -> twist_bones -> export_uploads -> transfer_uv) and the composed textures (compose_qfi.py):
# export -> normal convention -> queen LODs -> head material merged into the body -> material extras -> [--install]
# Usage: build_runtime.sh <creature lease token> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
token="$1"
cd "$repo"
tools/run_creature_blender.sh --token "$token" level_generation/creatures/mm6_qfi_claude/scripts/export_runtime.py
cd "$here"
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_qfi_lod0.glb export/mm6_qfi_runtime_lod0.glb | grep -E "normal map"
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_qfi_runtime_lod0.glb" \
  "$here/export/mm6_qfi_lods.glb" --mesh-node Queen 2>&1 | grep "LOD triangles"
python3 "$repo/tools/merge_head_material.py" export/mm6_qfi_lods.glb export/mm6_qfi.glb
python3 scripts/finish_runtime.py
rm -f export/mm6_qfi_lods.geometry.glb export/mm6_qfi_lods_q.glb
if [[ "${2:-}" == "--install" ]]; then
  cd "$repo"
  python3 tools/install_model.py level_generation/creatures/mm6_qfi_claude/export/mm6_qfi.glb --world mm6 | tail -1
fi
