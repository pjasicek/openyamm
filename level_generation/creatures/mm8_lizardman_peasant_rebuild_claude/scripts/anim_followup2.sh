#!/usr/bin/env bash
# Follow-up 2 (2026-11-12): the rebuild's mesh, textures and LODs with the original model's clips retargeted
# (scripts/retarget_orig.py, scripts/roles_orig.json), then the floor fix and the winding check ->
# export/mm8_lizardman_peasant.glb [--install]. Starts from the GLB installed when the follow-up was claimed
# (work/before_followup2/mm8_lizardman_peasant.glb); only the animations change.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
n=mm8_lizardman_peasant
PY=$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python
L=$repo/level_generation/creatures/claude_shared
export PYTHONPATH=$(python3 -c "import yaml,os;print(os.path.dirname(os.path.dirname(yaml.__file__)))")
cd "$here"; mkdir -p export
$PY scripts/retarget_orig.py work/before_followup2/$n.glb work/f2_clips.glb scripts/roles_orig.json 2>&1 | grep RETARGET
$PY $L/floor/floor_fix.py work/f2_clips.glb export/$n.glb $(cat scripts/floor_ops.txt) 2>&1 | grep -v Warning | tail -9
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/$n.glb | tail -1
if [[ " $* " == *" --install "* ]]; then (cd "$repo" && python3 tools/install_model.py "$here/export/$n.glb" --world mm8); fi
