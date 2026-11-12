#!/usr/bin/env bash
# rig blend -> body glb -> MM9 clips -> flat frames. Usage: TOKEN=<lease> scripts/quick.sh <tag>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
rel=level_generation/creatures/$(basename "$here"); tag=$1
(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" $rel/scripts/export_body.py "${BLEND:-$here/work/rig_$tag.blend}" "$here/work/rig_${tag}_body.glb" >/dev/null)
cd "$here"
PYTHONPATH=$(python3 -c "import yaml,os;print(os.path.dirname(os.path.dirname(yaml.__file__)))") ../claude_shared/gltf_venv/bin/python scripts/clips_mm9.py work/rig_${tag}_body.glb work/rig_${tag}_anim.glb scripts/roles_wwf.json work/clips_$tag.json 2>&1 | grep CLIPS
T=../claude_shared
python3 $T/motion_frames.py work/rig_${tag}_anim.glb Attack review/${tag}_attack.png --frames 6 --yaw 0.7 --cell 300 --highlight >/dev/null
python3 $T/motion_frames.py work/rig_${tag}_anim.glb Walking review/${tag}_walk.png --frames 5 --yaw 1.57 --cell 300 --highlight >/dev/null
python3 $T/motion_frames.py work/rig_${tag}_anim.glb Standing review/${tag}_stand.png --frames 3 --yaw 0.4 --cell 300 --highlight >/dev/null
