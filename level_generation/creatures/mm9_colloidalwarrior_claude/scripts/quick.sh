#!/bin/bash
# weights -> helpers -> reduce. Project folder.
R=$PWD
[[ -n "$SKIP_W" ]] || F='^(WRIST|REWEIGHT|RELAX)' scripts/run.sh weights_fix_cw.py $R/work/hands_v1.blend $R/work/wfix_v1.blend
[[ -n "$SKIP_W" ]] || F='^(HELPERS)' scripts/run.sh helpers_cw.py $R/work/wfix_v1.blend $R/work/help_v1.blend
F='^(DEC|protected|REDUCED)' scripts/run.sh reduce_cw.py $R/work/help_v1.blend $R/work/red_v1.blend
