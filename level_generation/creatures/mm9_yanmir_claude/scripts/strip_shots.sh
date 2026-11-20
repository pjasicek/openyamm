#!/bin/bash
# Viewer frame strips of every clip (6 frames each), one Chrome at a time (project folder). Then scripts/strip_sheets.sh.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
mkdir -p review/strips
S=$($G scripts/strips.py export/mm9_yanmir.glb 6 | tr '\n' ' ')
scripts/vsr.sh yanmir review/strips $S
