#!/bin/bash
# helpers -> quick glb -> clips -> half keys. Project folder.
R=$PWD; G=$R/../claude_shared/gltf_venv/bin/python
F='^(HELPERS)' scripts/run.sh helpers_nb.py $R/work/hands_v1.blend $R/work/help_v1.blend
F='^(LIFT|EXPORTED)|Traceback|Error' W=120 scripts/run.sh export_quick.py $R/work/help_v1.blend $R/work/quick_body.glb
$G scripts/clips_mm9.py work/quick_body.glb work/quick_clips.glb scripts/roles_nb.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-300 | tail -3
$G scripts/half_keys.py work/quick_clips.glb work/quick_half.glb 2>&1 | grep -v Unexpected | cut -c1-200 | tail -2
$G scripts/skirt_keys.py work/quick_half.glb work/quick_skirt.glb work/skirt_keys.json 2>&1 | grep -v Unexpected | tail -1 | cut -c1-120
