#!/bin/bash
# clean blend -> fit -> braid -> weights -> hands -> helpers (project folder)
S=$PWD
F='^FIT|Traceback|Error' W=300 scripts/run.sh fit_kira.py $S/work/clean_v1.blend $S/scripts/fit_kira.json $S/work/fit_v1.blend $S/work/fit_v1.json
F='^BRAID (length|done)|Traceback|Error' scripts/run.sh build_braid.py $S/work/fit_v1.blend $S/work/braid_v1.blend
F='^RIG skirt|Traceback|Error|^  File' W=300 scripts/run.sh rig_kira.py $S/work/braid_v1.blend $S/work/rig_v1.blend $S/work/rig_v1.json
F='^(GRAFT)|Traceback|Error|^  File' W=200 scripts/run.sh graft_hands.py $S/scripts/graft_kira.json
F='^(HELPERS)|Traceback|Error|^  File' scripts/run.sh helpers_kira.py $S/work/hands_v1.blend $S/work/help_v1.blend
