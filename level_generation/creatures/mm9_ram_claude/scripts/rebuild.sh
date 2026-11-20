#!/usr/bin/env bash
# ram export -> runtime -> viewer. Usage: scripts/rebuild.sh <sheep anim blend name> <revision>
set -euo pipefail
cd /home/pjasicek/github/OpenYAMM
. level_generation/creatures/mm9_sheep_claude/work/lease.env
P=level_generation/creatures/mm9_sheep_claude; R=level_generation/creatures/mm9_ram_claude
TAILN=6 $R/scripts/bl.sh $RAM_T $R/scripts/ram_export.py $PWD/$P/work/$1 $PWD/$R/work/anim_ram.blend $PWD/$R/export/mm9_ram_lod0.glb 0.4907 | grep -E "RAM_EXPORT|Error|Traceback|rc=" | cut -c1-120
python3 tools/creature_workspace.py run --project $R --token $RAM_T -- $R/scripts/build_runtime.sh 2>&1 | grep -E "LOD triangles|WINDING|corpse|Error|Traceback"
(cd $R; python3 scripts/viewer_tiers.py; python3 scripts/make_viewer_manifest.py $2 "ram_a=Ram (SHEEP2.dtx, RAMHORNBLACK.dtx)=review/viewer/ram_a.glb")
python3 tools/run_creature_review.py --project $R check 2>&1 | tail -4 | tr -d '\n'; echo
