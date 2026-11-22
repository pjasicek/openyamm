#!/usr/bin/env bash
# Far LODs by the LOD playbook ladder (project copy of lod_repair_claude/scripts in lodrepair/; Blender through the
# creature wrapper with the lease token), then verify only the far levels changed, stage export/xeen_feet.glb and
# check winding. Usage: TOK=<lease token> scripts/far_lods.sh
set -euo pipefail
cd "$(dirname "$0")/.."
repo="$(cd ../../.. && pwd)"
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py --source export/xeen_feet.glb xeen_feet | tail -2
chosen=$($LV -c "import json; print(json.load(open('lodrepair/work/xeen_feet/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/xeen_feet/installed.glb lodrepair/work/xeen_feet/$chosen.glb | tail -1
cp export/xeen_feet.glb export/xeen_feet_prelod.glb && cp lodrepair/export/xeen_feet.glb export/xeen_feet.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_feet.glb | tail -1
