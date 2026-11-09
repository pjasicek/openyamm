#!/usr/bin/env bash
# Reduced Genie runtime GLB from the picked ladder candidate: export_cand.py -> swap_lod0.py (into the rollback source:
# materials, variants, region ramps, clips, the lamp mesh and the collapsed-mesh node keys unchanged) -> build_lods.py ->
# shrink_shadow_lods.py -> carry_variants.py. Smooth shading -> export/mm7_m238.glb.
# Every step memory-capped (cap.sh / b.sh). Usage: TOKEN=<lease> scripts/build_export.sh [Cand_71] [ladder_d.blend]
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
out=export/mm7_m238.glb
cp work/${2:-ladder_d.blend} work/ladder.blend
REA_CAND=${1:-Cand_71} REA_NODE=M238 PAT="FLOOR|EXPORTED" scripts/b.sh export_cand.py
scripts/cap.sh python3 scripts/swap_lod0.py work/mm7_m238_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M238
scripts/cap.sh python3 scripts/strip_node_keys.py work/pick_lod0.glb
PAT="PROTECTED|RATIOS|LOD tri" scripts/b.sh build_lods.py
scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb $out
scripts/cap.sh python3 scripts/carry_variants.py $out
# the collapsed-mesh keys again (body hidden from 1.37 s of Death and in Dead, the lamp before 0.53 s of Death)
scripts/cap.sh python3 ../../../tools/model_hide_collapsed_meshes.py $out --write $out
ls -la $out
