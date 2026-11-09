#!/usr/bin/env bash
# weights trial: uv_v8 -> uv_<tag>, rebuild, fold numbers, Running viewer shots. Usage: run_try.sh <tag> (env REFINE_*, H_*)
cd /home/pjasicek/github/OpenYAMM
. level_generation/creatures/mm9_sheep_claude/work/lease.env; S=level_generation/creatures/mm9_sheep_claude; W=$PWD/$S/work
$S/scripts/bl.sh $SHEEP_T $S/scripts/refine_weights.py $W/uv_v8.blend $W/uv_$1.blend $W/refine_$1.json | grep -E "Error|Traceback" | cut -c1-200
$S/scripts/rebuild_export.sh uv_$1.blend $1 2>&1 | grep -E "WINDING|\"failed\": \[.+|Error|Traceback" | cut -c1-100
cd $S; for b in "hind:-0.4,0.4,0.1,0.8,0.15,1.1" "front:-0.4,0.4,-0.45,0.1,0.15,1.1"; do python3 scripts/fold_measure.py export/mm9_sheep.glb --box=${b#*:} 2>&1 | grep "^OVER" | sed "s/^OVER/${b%%:*}/" | cut -c1-170; done
cd ../../..; python3 tools/run_creature_review.py --project $S --token $SHEEP_T shots t5:Running:0.104:left:body t10:Running:0.208:left:body t15:Running:0.25:left:body t20:Running:0.05:quarter:body 2>&1 | tail -1
cd $S; python3 scripts/sheet.py work/try_$1.png 2 review/shots/t5.png review/shots/t10.png review/shots/t15.png review/shots/t20.png; python3 -c "
from PIL import Image; im=Image.open('work/try_$1.png'); im.resize((im.width*3//4, im.height*3//4),Image.LANCZOS).save('work/try_$1.png')"; echo DONE
