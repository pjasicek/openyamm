#!/bin/bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_troglodyte_claude; . scripts/env.sh
until grep -q CYCLEDONE work/cycle.log; do sleep 3; done
$G scripts/collapse_gate.py export/mm9_troglodyte.glb review/gates/collapse_bindref.json 2>/dev/null > review/gates/collapse_bindref.txt &
cd $REPO; env -u PYTHONPATH python3 level_generation/projects/mm9r_common/review_root.py > /dev/null 2>&1
./build/game/openyamm --world mm9 --headless-run-regression-suite actors > level_generation/creatures/mm9_troglodyte_claude/work/regression2.log 2>&1 &
cd $P; scripts/deliver.sh > work/deliver.log 2>&1
cd $REPO; python3 tools/run_creature_review.py --project level_generation/creatures/mm9_troglodyte_claude check > $P/work/check.log 2>&1
python3 tools/run_creature_review.py --project level_generation/creatures/mm9_troglodyte_claude --token $TOKEN playback > $P/work/playback.log 2>&1
wait
echo POSTDONE > $P/work/post.done
