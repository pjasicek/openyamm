#!/bin/bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_troglodyte_claude; . scripts/env.sh
scripts/rebuild.sh --install 2>&1 | grep -E 'WINDING|Error|Traceback' | cut -c1-120
scripts/viewer_update.sh r12 | cut -c1-40
$G scripts/head_ref.py 2>&1 | tail -1
CLIPS=Standing,Hit,Hit2,Taunt,Death,Dead $G scripts/collapse_gate.py export/mm9_troglodyte.glb review/gates/collapse_fix.json 2>/dev/null > review/gates/collapse_fix.txt
cd $REPO; env -u PYTHONPATH python3 level_generation/projects/mm9r_common/review_root.py >/dev/null 2>&1
./build/game/openyamm --world mm9 --headless-run-regression-suite actors > $P/work/regression3.log 2>&1
echo FIXDONE
