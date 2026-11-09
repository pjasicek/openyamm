#!/bin/bash
# weights -> export -> runtime -> viewer (cow|goat)
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures; C=$P/mm9_$1_claude; B=$P/mm9_cow_claude/scripts/bl.sh; n=$1
T=29ba4377adce484f9aa6c355f3fd7af2; [ $n = goat ] && T=c1eeb181c57e41268a1982e91e7b6b22
if [ $n = cow ]; then export FOOT_R=0.14 FOOT_TOP=0.02 FOOT_BLEND=0.05 UDDER=0.5,1.2,0.7,0.2,XbackC; else export FOOT_R=0.07 FOOT_TOP=0.015 FOOT_BLEND=0.03; fi
GREP="^REFINE|Error|line [0-9]" $B $n refine_weights.py $C/work/uv_v1.blend $C/work/uv_v1r.blend $C/work/refine_v1.json | cut -c1-260
GREP="^WEIGHTS2|Error|line [0-9]" $B $n weights_v2.py $C/work/uv_v1r.blend $C/work/uv_v2.blend $C/work/weights_v2.json | cut -c1-200
GREP="^EXPORTED|Error|line [0-9]" $B $n build_export.py $C/work/uv_v2.blend $C/work/anim_v2.blend $C/export/mm9_${n}_lod0.glb $C/work/clips_v2.json | cut -c1-200
python3 tools/creature_workspace.py run --project $C --token $T -- $C/scripts/build_runtime.sh $2 2>&1 | grep -E "LOD triangles|WINDING|^(Standing|Walking|Running|Dead|Fidget|Hit|AttackMelee):|rror" | cut -c1-140
