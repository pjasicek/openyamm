#!/bin/bash
# quick look at the fist: parts_r4 -> export -> pivot -> clips -> fist keys -> four textured views of the right hand (project folder)
R=$PWD; G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
F='^(EXPORTED|Trace)' scripts/run.sh export_yan.py $R/work/parts_r4.blend $R/work/g_body.glb > /dev/null
$G scripts/head_pivot.py work/g_body.glb work/g_body_p.glb 0 0.02 -0.06 > /dev/null
$G scripts/clips_mm9.py work/g_body_p.glb work/g_c0.glb scripts/roles_yan.json /dev/null 2>&1 | grep -E 'Error|Trace'
$G scripts/finger_keys_yan.py work/g_c0.glb work/g_c1.glb work/hand_poses.json > /dev/null
i=0; for v in -1:-0.3:0.1 0:-1:0.1 -0.3:1:0.2 1:-0.2:0.1; do i=$((i+1)); C=-0.55,-0.25,1.5 COLOR=TEXTURE RES=500 CLIPS='Standing@0' /snap/bin/blender --background --factory-startup --python scripts/pose_strip.py -- work/g_c1.glb work/views/fq_$i.png $v ${ORTHO:-0.45} 2>&1 | grep -E "Error|Trace"; python3 scripts/strip_join.py work/views/fq_$i.png 1 > /dev/null; done
python3 -c "
from PIL import Image
s=Image.new('RGB',(2000,500))
for i in range(4): s.paste(Image.open(f'work/views/fq_{i+1}.png'),(i*500,0))
s.save('work/views/fq_sheet.png')"
