#!/usr/bin/env bash
# Rebake Attack v2 into the m532 master and gate it. Prints the bake residuals, the gate summary and per-frame rows.
cd /home/pjasicek/github/OpenYAMM
S=level_generation/creatures/mm8_centaur_reduce_claude/attack_v2/scripts; W=$PWD/level_generation/creatures/mm8_centaur_reduce_claude/attack_v2/work
M=level_generation/creatures/mm8_m532_claude
$S/rb.sh $M/scripts/animate_attack_v2.py | grep -E "ATTACK_V2|RESIDUALS|Error|Traceback|line [0-9]" | cut -c1-600
$S/rb.sh $M/scripts/attack_gate.py $PWD/$M/work/centaur_master_attack_v2.blend $W/gate_v2.json | grep -E "^GATE|Error|Traceback" | cut -c1-900
python3 - "$W/gate_v2.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))['rows']
for r in d:
    print(r['f'], 'wr', r['wrist_L'], r['wrist_R'], 'tw', r['twist_L'], r['twist_R'], 'el', r['elbow_twist_L'],
          r['elbow_twist_R'], 'nock', r['nock_to_finger_mm'], 'step', r['largest_step'])
PY
