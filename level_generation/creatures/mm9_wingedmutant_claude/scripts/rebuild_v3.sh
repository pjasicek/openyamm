#!/usr/bin/env bash
# Texture quality pass 2026-10-30 (README "Texture quality pass"): rebuild_v2.sh with the new UVs. uv_v1.blend ->
# graft -> symmetrize -> texture-pass UVMap + HeadUV (carried from work/uv_texpass2.blend, which retexture_v2 and the
# head relayout were made on) -> wing back faces -> head set -> animated export -> runtime GLB [--install].
# The one-time texture steps (dump_regions, AO bake, compose.py, grade, resample_head.py) are listed in the README.
# Run from the repository root with TOKEN=<lease>.
set -euo pipefail
P=level_generation/creatures/mm9_wingedmutant_claude
R="$PWD"; W="$R/$P/work"; : "${TOKEN:?set TOKEN}"
B() { /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 --python "$@" 2>&1 \
      | grep -E "GRAFT |SYMMETRIZED|TEXPASS|BACKFACES|DUMPHEAD|Error|Traceback" | cut -c1-300 || true; }
B $P/scripts/graft_head.py -- $W/uv_v1.blend $R/$P/meshy/head_smart_v1/model_urls_glb.glb $P/scripts/graft_config.json $W/graft_v2.blend $P/work/graft_v2.json >/dev/null
B $P/scripts/symmetrize.py -- $W/graft_v2.blend $W/sym_v2.blend $P/work/sym_v2.json
B $P/scripts/transfer_texpass_uv.py -- $W/uv_texpass2.blend $W/sym_v2.blend $W/head_v5.blend
B $P/scripts/add_backfaces.py -- $W/head_v5.blend $W/head_v6.blend 0.002
B $P/scripts/dump_head.py -- $W/head_v6.blend $W/head_v6.npz
python3 $P/scripts/compose_head.py head_v6.npz | cut -c1-200
tools/run_creature_blender.sh --token "$TOKEN" $P/scripts/build_export.py $W/head_v6.blend $W/anim_v4.blend $R/$P/export/mm9_wingedmutant_lod0.glb $P/work/clips_v4.json
python3 tools/creature_workspace.py run --project $P --token "$TOKEN" -- $P/scripts/build_runtime.sh "$@"
python3 $P/scripts/viewer_tiers.py
