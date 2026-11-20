#!/bin/bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_troglodyte_claude; . scripts/env.sh
until grep -q FIXDONE work/fix.log; do sleep 4; done
$G scripts/head_build.py work/eye_r.npz 2>&1 | grep -E 'Error|Trace'
$G scripts/join.py 2>&1 | grep -E 'Error|Trace'
scripts/rebuild.sh --install 2>&1 | grep -E 'WINDING|Error|Traceback' | cut -c1-120
scripts/viewer_update.sh r13 | cut -c1-40
CLIPS=Standing,Hit,Hit2,Taunt,Death,Dead $G scripts/collapse_gate.py export/mm9_troglodyte.glb review/gates/collapse_fix.json 2>/dev/null > review/gates/collapse_fix.txt
cd $REPO; env -u PYTHONPATH python3 level_generation/projects/mm9r_common/review_root.py >/dev/null 2>&1
(./build/game/openyamm --world mm9 --headless-run-regression-suite actors > $P/work/regression4.log 2>&1 & R=$!; until grep -q "mm9_actor_models_build_every_binding" $P/work/regression4.log 2>/dev/null; do sleep 4; done; kill $R)
echo JAWDONE
