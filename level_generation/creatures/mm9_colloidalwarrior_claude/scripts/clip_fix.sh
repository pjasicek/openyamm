#!/bin/bash
# clip corrections (project folder). In: work/cw_ref_clips.glb (MM9 clips, head cap, helpers), out: work/cw_final_clips.glb
# 1. hands cleared on keys (hand_clear_keys.py, every clip and side with a contact);
# 2. a second pass with the larger grid for AttackRanged R (the hand scooping slime went 15 cm into the chest; cleared it lies
#    on the belly) and BackpedalRun L with 0.25 s ramps (0.4 s ramps found no solution);
# 3. exact helpers.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
"$G" scripts/hand_clear_keys.py work/cw_ref_clips.glb work/cw_clips3.glb work/hand_clear.json 2>&1 | grep -E 'CLEAR|NOFIX|DONE|Error|Traceback' | cut -c1-200
HC_BIG=1 "$G" scripts/hand_clear_keys.py work/cw_clips3.glb work/cw_clips4.glb work/hand_clear_big.json AttackRanged:R BackpedalRun:L:0.25 2>&1 | grep -E 'CLEAR|NOFIX|DONE|Error|Traceback' | cut -c1-200
"$G" scripts/half_keys.py work/cw_clips4.glb work/cw_final_clips.glb 2>&1 | tail -1
