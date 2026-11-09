#!/usr/bin/env bash
# compose -> export -> runtime -> viewer (sheep). Usage: scripts/rebuild_export.sh <uv blend> <tag>
set -euo pipefail
cd /home/pjasicek/github/OpenYAMM
. level_generation/creatures/mm9_sheep_claude/work/lease.env
P=level_generation/creatures/mm9_sheep_claude; W=$PWD/$P/work
TAILN=6 $P/scripts/bl.sh $SHEEP_T $P/scripts/build_export.py $W/$1 $W/anim_$2.blend $PWD/$P/export/mm9_sheep_lod0.glb $W/clips_$2.json | grep -E "EXPORTED|Error|Traceback|rc=" | cut -c1-300
python3 tools/creature_workspace.py run --project $P --token $SHEEP_T -- $P/scripts/build_runtime.sh 2>&1 | grep -E "LOD triangles|WINDING|raised|grounded|corpse|Error|Traceback"
(cd $P; python3 scripts/viewer_tiers.py; python3 scripts/make_viewer_manifest.py r_$2 "sheep_a=Ewe, Bori, Ratatosk (SHEEP1.dtx)=review/viewer/sheep_a.glb")
python3 tools/run_creature_review.py --project $P check 2>&1 | tail -4 | tr -d '\n'; echo
