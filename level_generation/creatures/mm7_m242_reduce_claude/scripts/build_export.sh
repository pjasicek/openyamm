#!/usr/bin/env bash
# Reduced Ghost runtime GLB from the picked ladder candidate: export_cand.py -> swap_lod0.py (into the rollback source:
# materials, variants, region ramps and clips unchanged) -> build_lods.py -> shrink_shadow_lods.py -> carry_variants.py.
# Smooth shading as the source. Every step memory-capped (cap.sh). Usage: TOKEN=<lease> scripts/build_export.sh [blend] [Cand_82]
set -euo pipefail
cd "$(dirname "$0")/.."
blend=${1:-ladder_h.blend}; cand=${2:-Cand_82}; out=export/mm7_m242.glb
cp work/$blend work/ladder.blend
REA_CAND=$cand REA_NODE=M242 PAT="FLOOR|EXPORTED" scripts/b.sh export_cand.py
CAP=6G scripts/cap.sh python3 scripts/swap_lod0.py work/mm7_m242_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M242
REA_LOD_RATIOS=${REA_LOD_RATIOS:-0.5,0.2,0.07} REA_NODE=M242 PAT="PROTECTED|RATIOS|LOD tri" scripts/b.sh build_lods.py
REA_NODE=M242 CAP=6G scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb $out
CAP=6G scripts/cap.sh python3 scripts/carry_variants.py $out
ls -la $out
