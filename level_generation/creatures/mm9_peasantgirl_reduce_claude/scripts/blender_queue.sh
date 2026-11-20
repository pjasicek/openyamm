#!/bin/bash
# One Blender at a time: see-through (every clip) and LOD checks, installed and candidate, both GLBs.
# Usage (project folder): scripts/blender_queue.sh <cand tag>   (export/cand_<tag>/)
set -u
cd "$(dirname "$0")/.."; t=$1
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
scripts/see_through.sh export/cand_$t/mm9_peasantgirl.glb ${t}_h
scripts/see_through.sh export/cand_$t/mm9_peasantgirl1e.glb ${t}_e
REA_NODE=PeasantGirl $BL -P scripts/lod_check.py -- $PWD/export/cand_$t/mm9_peasantgirl.glb ${t}_h > work/lod_check_${t}_h.log 2>&1
REA_NODE=PeasantGirl $BL -P scripts/lod_check.py -- $PWD/export/cand_$t/mm9_peasantgirl1e.glb ${t}_e > work/lod_check_${t}_e.log 2>&1
if [[ ! -f work/lod_check_inst_h.json ]]; then
  REA_NODE=PeasantGirl $BL -P scripts/lod_check.py -- $PWD/before/mm9_peasantgirl.glb inst_h > work/lod_check_inst_h.log 2>&1
  REA_NODE=PeasantGirl $BL -P scripts/lod_check.py -- $PWD/before/mm9_peasantgirl1e.glb inst_e > work/lod_check_inst_e.log 2>&1
fi
if [[ ! -f review/gates_before_h/see_through.json ]]; then
  scripts/see_through.sh before/mm9_peasantgirl.glb before_h
  scripts/see_through.sh before/mm9_peasantgirl1e.glb before_e
fi
echo QUEUEDONE > work/blender_queue_$t.done
