#!/bin/bash
VIEWER_OK=1 REV=r5 scripts/rebuild.sh --install 2>&1 | grep -E 'WINDING|stretching|Traceback|^Error|source:|manifest' | cut -c1-90
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
$G scripts/grip_gate.py work/trell_final_clips.glb 2>/dev/null | sed -n 1p | cut -c1-100
$G scripts/wrist_gate.py export/mm9_trellborg.glb 2>/dev/null | grep WRISTGATE | cut -c1-140
cd ../../..; python3 level_generation/projects/mm9r_common/review_root.py 2>&1 | tail -1 | cut -c1-50
timeout 200 ./build/game/openyamm --world mm9 --headless-run-regression-suite actors > level_generation/creatures/mm9_trellborg_claude/review/gates/regression.txt 2>&1
grep -E 'mm9_actor_models_build_every_binding' level_generation/creatures/mm9_trellborg_claude/review/gates/regression.txt | tail -1 | cut -c1-70
python3 tools/run_creature_review.py --project level_generation/creatures/mm9_trellborg_claude check 2>&1 | grep -c '"failed": \[\]'
echo R5_DONE
