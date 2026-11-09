#!/bin/bash
# helpers -> reduce -> quick glb -> clips. Project folder.
R=$PWD; G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
F='^(HELPERS)' scripts/run.sh helpers_thrall.py $R/work/hands_v1.blend $R/work/help_v1.blend
F='^(DEC|protected|REDUCED)' scripts/run.sh reduce_thrall.py $R/work/help_v1.blend $R/work/red_v1.blend
F='^(LIFT|EXPORTED)' scripts/run.sh export_quick.py $R/work/red_v1.blend $R/work/quick_body.glb
$G scripts/clips_mm9.py work/quick_body.glb work/quick_clips.glb scripts/roles_thrall.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-260
