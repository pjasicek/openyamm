#!/usr/bin/env bash
# Rig stage (project folder): weights -> GLB -> clips -> grip -> half joints -> [arm fixes: arm_stage.sh] -> floor -> coat and tabard keys -> floor.
# Writes work/rig_out.glb (textures not yet final). Usage: scripts/rig_stage.sh
set -euo pipefail
G=../claude_shared/gltf_venv/bin/python
python3 scripts/weights_lk.py work/asm4.npz work/heat.npz work/rig.json work/finger_labels.npy work/weights.npz | tail -1
"$G" -W ignore scripts/build_glb_lk.py ${UVNPZ:-work/uv_v1.npz} work/weights.npz work/body.glb 2>&1 | tail -1
"$G" -W ignore scripts/clips_lk.py work/body.glb work/clips.glb scripts/roles_lk.json work/clips.json 2>&1 | grep -E "Traceback|Error" || true
"$G" -W ignore scripts/arm_out.py work/clips.glb work/clips_o.glb ${ARMOUT:-R:8 L:5} | tail -2
"$G" -W ignore scripts/grip_keys.py work/clips_o.glb work/clips_g0.glb work/rig.json work/grip.json | tail -5
"$G" -W ignore scripts/staff_lean.py work/clips_g0.glb work/clips_g.glb ${STAFF_LEAN:-1.0} | grep -E "STAFF|Standing|Error|Trace"
"$G" -W ignore scripts/half_keys.py work/clips_g.glb work/half.glb 2>&1 | grep -E "Traceback|Error|HALF" || true
bash scripts/floor.sh work/half.glb work/pre_coat.glb >/dev/null
"$G" -W ignore scripts/coat_keys.py work/pre_coat.glb work/coat.glb work/rig.json work/asm4.npz work/coat.json 2>&1 | grep -E "Traceback|Error" || true
# r11: the head ducks 30 deg sideways as the left hand sweeps over the crown in AttackMelee (instead of an arm correction that failed jitter)
mv work/coat.glb work/coat0.glb; "$G" -W ignore scripts/head_duck.py work/coat0.glb work/coat.glb AttackMelee 18.5 30 0.12 | grep HEADDUCK
# 2026-11-01: the staff seated in the palm (2 cm) met the head 2.1 cm deep in Hit (2 frames; r13 1.2 cm): the head turns 20 deg off its skull
mv work/coat.glb work/coat1.glb; "$G" -W ignore scripts/head_duck.py work/coat1.glb work/coat.glb Hit 7.5 20 0.06 staff | grep HEADDUCK
cur=work/coat.glb
if [[ -x scripts/arm_stage.sh ]]; then bash scripts/arm_stage.sh $cur work/arms.glb; cur=work/arms.glb; fi
bash scripts/floor.sh $cur work/rig_out.glb >/dev/null
ls -la work/rig_out.glb
