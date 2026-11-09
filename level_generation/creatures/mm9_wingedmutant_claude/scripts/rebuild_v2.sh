#!/usr/bin/env bash
# Rework 2026-10-30 (symmetry, grafted head with its own 1K head set): uv_v1.blend -> graft -> symmetrize -> HeadUV
# (carried from work/head_v1.blend, which the paid head retexture was painted on) -> wing back faces -> head set ->
# animated export -> runtime GLB [--install]. Run from the repository root with TOKEN=<lease>.
set -euo pipefail
P=level_generation/creatures/mm9_wingedmutant_claude
R="$PWD"; W="$R/$P/work"; : "${TOKEN:?set TOKEN}"
B() { /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 --python "$@" 2>&1 \
      | grep -E "GRAFT |SYMMETRIZED|HEADUV|BACKFACES|DUMPHEAD|Error|Traceback" | cut -c1-300 || true; }
B $P/scripts/graft_head.py -- $W/uv_v1.blend $R/$P/meshy/head_smart_v1/model_urls_glb.glb $P/scripts/graft_config.json $W/graft_v2.blend $P/work/graft_v2.json >/dev/null
B $P/scripts/symmetrize.py -- $W/graft_v2.blend $W/sym_v2.blend $P/work/sym_v2.json
# head_v1.blend: work/sym_v1 + scripts/head_uv.py (args 4.5 75 88); its HeadUV and upload fed head_retexture_v1
B $P/scripts/transfer_headuv.py -- $W/head_v1.blend $W/sym_v2.blend $W/head_v3.blend
B $P/scripts/add_backfaces.py -- $W/head_v3.blend $W/head_v4.blend 0.002
B $P/scripts/dump_head.py -- $W/head_v4.blend $W/head_v4.npz
python3 $P/scripts/compose_head.py head_v4.npz | cut -c1-200
tools/run_creature_blender.sh --token "$TOKEN" $P/scripts/build_export.py $W/head_v4.blend $W/anim_v3.blend $R/$P/export/mm9_wingedmutant_lod0.glb $P/work/clips_v3.json
python3 tools/creature_workspace.py run --project $P --token "$TOKEN" -- $P/scripts/build_runtime.sh "$@"
python3 $P/scripts/viewer_tiers.py
