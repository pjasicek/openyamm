#!/usr/bin/env bash
# Attack v2 + bow-carry fix: rebake Attack, re-hold every other clip, export LOD0, gate every clip.
cd /home/pjasicek/github/OpenYAMM
S=level_generation/creatures/mm8_centaur_reduce_claude/attack_v2/scripts; M=level_generation/creatures/mm8_m532_claude
W=$PWD/level_generation/creatures/mm8_centaur_reduce_claude/attack_v2/work/carry; B=$PWD/$M/work/centaur_master_carry.blend
$S/rb.sh $M/scripts/animate_attack_v2.py | grep -E "ATTACK_V2|RESIDUALS|Error|Traceback" | cut -c1-300
$S/rb.sh $M/scripts/carry_fix.py $PWD/$M/work/centaur_master_attack_v2.blend $B | grep -E "CARRY |Error|Traceback" | cut -c1-300
$S/rb.sh $M/scripts/export_master_lod0.py $B $PWD/$M/work/carry_lod0.glb | grep -E "EXPORTED|Error"
$S/rb.sh $M/scripts/hold_match.py $B Standing:0 Attack:0 Attack:72 Standing:96 Hit:0 Hit:42 Cast:0 Cast:72 Fidget:0 Fidget:60 | grep MATCH
for a in Standing Walking Running Fidget Hit Cast Death Dead Attack; do
    $S/rb.sh $M/scripts/attack_gate.py $B $W/after_$a.json $a | grep -E "Error|Traceback"
    $S/rb.sh $M/scripts/arm_body_probe.py $B $a all | grep WORST | cut -c1-160
    python3 - "$W" "$a" <<'PY'
import json, sys
W, a = sys.argv[1:]; b = json.load(open(f'{W}/before_{a}.json'))['summary']; s = json.load(open(f'{W}/after_{a}.json'))['summary']
print('GATE', a, 'bow wrist', b['max_wrist_L'], '->', s['max_wrist_L'], '| draw wrist', s['max_wrist_R'], '| twist L', s['max_abs_twist_L'],
      'elbow', s['max_abs_elbow_twist_L'], '| twist step', round(s['max_twist_step'], 1), '| largest step', s['largest_bone_step'],
      '| arm in torso', s['max_arm_in_torso_depth_mm'], '| lowest', b['lowest_z_mm'], '->', s['lowest_z_mm'])
PY
done
