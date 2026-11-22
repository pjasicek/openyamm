#!/usr/bin/env bash
set -euo pipefail; here=$PWD; repo=$(cd ../../.. && pwd)
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py --source export/xeen_hand_prelod.glb \
  xeen_hand | tail -2
chosen=$($LV -c "import json; print(json.load(open('lodrepair/work/xeen_hand/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/xeen_hand/installed.glb lodrepair/work/xeen_hand/$chosen.glb | tail -1
cp lodrepair/export/xeen_hand.glb export/xeen_hand.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_hand.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_hand.glb --world xeen
fi
ls -la export/xeen_hand.glb
