#!/bin/bash
# helpers -> reduce -> quick glb -> clips. Project folder.
R=$PWD; G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
F='^(WRIST|REWEIGHT)' scripts/run.sh weights_trell.py $R/work/hands_v1.blend $R/work/wfix_v1.blend
F='^(HELPERS)' scripts/run.sh helpers_trell.py $R/work/wfix_v1.blend $R/work/help_v1.blend
F='^(DEC|protected|REDUCED)' scripts/run.sh reduce_trell.py $R/work/help_v1.blend $R/work/red_v1.blend
$G scripts/make_club.py 2>&1 | tail -1
F='^(CLUB)' scripts/run.sh add_club.py $R/work/red_v1.blend $R/work/redc_v1.blend
F='^(LIFT|EXPORTED)' scripts/run.sh export_quick.py $R/work/redc_v1.blend $R/work/quick_body.glb
$G scripts/clips_mm9.py work/quick_body.glb work/quick_clips0.glb scripts/roles_trell.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-260
$G scripts/club_keys.py work/quick_clips0.glb work/quick_clips0c.glb work/grip.json 2>&1 | tail -1 | cut -c1-300
$G scripts/half_keys.py work/quick_clips0c.glb work/quick_clips.glb 2>&1 | tail -1 | cut -c1-200
