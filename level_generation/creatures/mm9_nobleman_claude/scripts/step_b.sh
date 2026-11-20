#!/bin/bash
# rig -> hands -> helpers. Project folder.
S=$PWD
F='^(RIG)|Traceback|Error|^  File' W=${W:-400} scripts/run.sh rig_nb.py $S/work/graft_v1.blend $S/work/rig_v1.blend $S/work/rig_v1.json
F='^(WRIST|OBJ|RING|FINAL|GRAFT|HANDS)|Traceback|Error|^  File' W=${W:-300} scripts/run.sh graft_hands.py $S/scripts/graft_nb.json
F='^(HELPERS)|Traceback|Error|^  File' scripts/run.sh helpers_nb.py $S/work/hands_v1.blend $S/work/help_v1.blend
