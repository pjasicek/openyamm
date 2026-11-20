#!/bin/bash
# weights -> helpers -> reduce -> quick glb -> clips. Project folder.
R=$PWD; G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
[[ -n "$SKIP_W" ]] || F='^(WRIST|REWEIGHT)' scripts/run.sh weights_fix_yan.py $R/work/hands_v1.blend $R/work/wfix_v1.blend
[[ -n "$SKIP_W" ]] || F='^(HELPERS)' scripts/run.sh helpers_yan.py $R/work/wfix_v1.blend $R/work/help_v1.blend
F='^(DEC|protected|REDUCED)' scripts/run.sh reduce_yan.py $R/work/help_v1.blend $R/work/red_v1.blend
