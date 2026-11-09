#!/bin/bash
# rig -> hands -> weld. Project folder.
R=$PWD
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_thrall_claude; T=$(cat $P/work/token); cd $P
F='^(RIG |Trace)' W=200 scripts/run.sh rig_thrall.py $R/work/graft_v1.blend $R/source/true/thrall1_true.glb $R/work/pose_v1.blend.joints.npz $R/work/rig_v1.blend | grep -E 'zero|Trace|Error'
cd ../../..; out=$(tools/run_creature_blender.sh --token $T $P/scripts/graft_hands.py $R/scripts/graft_thrall.json 2>&1); L=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1); grep -E 'Traceback|Error|^  File' $L | cut -c1-300; cd $P
F='^(WRIST)' W=240 scripts/run.sh wrist_weld.py $R/work/hands_raw.blend $R/work/hands_v1.json $R/work/hands_v1.blend
F=NOPE scripts/run.sh view_hands.py $R/work/hands_v1.blend $R/work/vh
python3 - <<'P'
from PIL import Image
s=Image.new('RGB',(6*420,420))
for k,v in enumerate(['L_out','L_front','L_in','R_out','R_front','R_in']):
    s.paste(Image.open(f'work/vh_{v}.png').convert('RGB').resize((420,420)),(k*420,0))
s.save('work/_vh.png')
P
