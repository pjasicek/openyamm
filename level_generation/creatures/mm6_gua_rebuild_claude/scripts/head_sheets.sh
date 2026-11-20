#!/usr/bin/env bash
# Head shots for acceptance: every tier, six views, 1200 px sheets. Usage: scripts/head_sheets.sh [out dir]
set -uo pipefail
PY=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
U=http://127.0.0.1:8912/level_generation/creatures/mm9_guard_claude/review/viewer/
O=${1:-review/head3}
for t in a b c; do
  S=$($PY scripts/close_specs.py review/viewer/guard_$t.glb h "Standing:0.5" "Bip01 Head:0,0.15,1:0.42" "Bip01 Head:0.7,0.15,1:0.42" "Bip01 Head:1,0.15,0:0.42" "Bip01 Head:-1,0.15,0:0.42" "Bip01 Head:0,0.15,-1:0.42" "Bip01 Head:0.25,-0.8,1:0.42" 2>/dev/null | python3 -c "
import sys
for l in sys.stdin:
    p=l.strip().split(':'); a=[float(x) for x in p[5].split(',')]; b=[float(x) for x in p[6].split(',')]; a[1]+=.09; b[1]+=.09
    print(':'.join(p[:5]+[','.join(f'{x:.3f}' for x in a),','.join(f'{x:.3f}' for x in b)]),end=' ')")
  node ../mm8_m424_claude/scripts/viewer_shots.mjs "$U?model=guard_$t" $O/$t $S > /dev/null 2>&1
  python3 scripts/shots_sheet.py review/head_$t.png 3 640 $O/$t/h*.png > /dev/null
done
