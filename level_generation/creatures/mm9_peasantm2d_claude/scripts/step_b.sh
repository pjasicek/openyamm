#!/bin/bash
# rig -> hands -> helpers. Project folder. IN = rest-fitted blend (default work/fit_v1.blend)
S=$PWD
F='^(RIG)|Traceback|Error' W=${W:-400} scripts/run.sh rig_pm2.py $S/work/${IN:-fit_v1.blend} $S/work/rig_v1.blend $S/work/rig_v1.json
F='^(GRAFT|HANDS)|Traceback|Error|^  File' W=${W:-300} scripts/run.sh graft_hands.py $S/scripts/graft_pm2.json
F='^(HELPERS|RELAX)|Traceback|Error|^  File' scripts/run.sh helpers_pm2.py $S/work/hands_v1.blend $S/work/help_v1.blend
