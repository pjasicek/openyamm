#!/bin/bash
# HOF2 variant geometry chain (repo root): (fit_rig.py on work/hof2/variant_v1.glb with phof2c first) reduce -> bracelets
# -> MPFB hands -> neck cut -> ears -> head split. FROM=<n> skips the first n-1 steps.
set -e
P=level_generation/creatures/mm9_peasanthof_claude; W=$PWD/$P/work/hof2; S=$P/scripts; F=${FROM:-1}
[ $F -le 1 ] && $S/bld.sh "REDUCE|Error|Trace" $S/reduce_uv.py $W/fit_v1.blend $W/rig_v1.blend $PWD/$P/texturing/phof2_upload_smartuv.glb $W/rig_v1.json $PWD/$S/reduce_config.json
[ $F -le 2 ] && $S/bld.sh "BRACELETS|Error|Trace" $S/drop_bracelets.py $W/rig_v1.blend $W/rig_v2.blend
[ $F -le 3 ] && $S/bld.sh "^GRAFT|Error|Trace" $S/graft_hands.py $PWD/$S/graft_phof2.json | cut -c1-200
[ $F -le 4 ] && $S/bld.sh "NECKCUT|Error|Trace" $S/neck_bisect.py $W/hands_v1.blend $W/hands_v3.blend 0.635 0.16
[ $F -le 5 ] && EAR_X=0.092 EAR_Y=0.015 EAR_Z=0.785 EAR_DIR=0.78,0.28,0.56 EAR_LEN=0.09 $S/bld.sh "EARS|EAR hits|Error|Trace" $S/add_ears.py $W/hands_v3.blend $W/ears_v1.blend
[ $F -le 6 ] && $S/bld.sh "HEADSPLIT|Error|Trace" $S/head_split.py $PWD/$S/head_phof2.json | cut -c1-300
echo GEO2DONE
