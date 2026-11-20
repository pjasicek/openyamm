#!/bin/bash
# rig -> hands -> helpers. Project folder.
S=$PWD
F='^(RIG)|Traceback|Error' W=${W:-400} scripts/run.sh rig_nj.py $S/work/graft_v1.blend $S/work/rig_v1.blend $S/work/rig_v1.json
F='^(GRAFT|HANDS)|Traceback|Error|^  File' W=${W:-300} scripts/run.sh graft_hands.py $S/scripts/graft_nj.json
F='^(HELPERS|RELAX)|Traceback|Error|^  File' scripts/run.sh helpers_nj.py $S/work/hands_v1.blend $S/work/help_v1.blend
