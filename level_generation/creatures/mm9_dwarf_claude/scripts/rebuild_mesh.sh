#!/usr/bin/env bash
# Meshy returns -> reduced symmetric body -> rest fit -> head -> weights -> hands -> gloves -> helpers -> UVs. Never after the UV upload went to Meshy. Project folder.
set -uo pipefail
R=$PWD
F='^(CLEAN)' W=300 scripts/run.sh clean_dwarf.py $R/meshy/dwarf_smart_v1/model_urls_glb.glb $R/source/true/dwarf_true.glb $R/work/clean_v1.blend $R/work/clean_v1.json
F='^(HIDDEN holes|OBJ Face|Tra)' W=170 HEAD_TRIS=${HEAD_TRIS:-3300} scripts/run.sh head_prep_dwarf.py $R/meshy/dwarf_head_smart_v1/model_urls_glb.glb $R/work/head_parts.blend | tail -2
F='^FIT' W=100 scripts/run.sh fit_dwarf.py $R/work/clean_v1.blend $R/scripts/fit_dwarf.json $R/work/fit_v1.blend $R/work/fit_v1.json
F='^(BRIDGE|FINAL)' W=200 scripts/run.sh graft_head_dwarf.py $R/work/fit_v1.blend $R/work/head_parts.blend $R/work/graft_v1.blend | tail -2
F='^(RIG)' W=200 scripts/run.sh rig_dwarf.py $R/work/graft_v1.blend $R/work/rig_v1.blend $R/work/rig_v1.json
F='^(GRAFT)' W=200 scripts/run.sh graft_hands.py $R/scripts/graft_dwarf.json | tail -1
F='^(GLOVE)' scripts/run.sh glove_dwarf.py $R/work/hands_v1.blend $R/work/hands_v2.blend
F='^(HELPERS)' scripts/run.sh helpers_dwarf.py $R/work/hands_v2.blend $R/work/help_v1.blend
F='^(FACES|USE|UVDONE)' W=300 scripts/run.sh uv_dwarf.py $R/work/help_v1.blend $R/work/uv_v1.blend $R/texturing/dwarf_body_upload.glb $R/work/uv_report.json
echo MESH_DONE
