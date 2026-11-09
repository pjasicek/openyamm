#!/usr/bin/env bash
# After the Meshy return: UV parity, raster, AO, compose, geometry export, swap into the installed GLB (clips and
# variants kept), maps swapped in, LODs, shadow LODs, variant mappings, viewer tiers (tag rt).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
t(){ local s=$(date +%s); "$@" > "$P/work/log_chain_$(basename "${@: -1}").txt" 2>&1 || { echo "FAILED $*"; tail -20 "$P/work/log_chain_$(basename "${@: -1}").txt"; exit 1; }; echo "$* $(( $(date +%s) - s ))s" | cut -c1-140; }
t blender -b -P scripts/verify_uv.py
t blender -b -P scripts/uv_raster.py
t blender -b -P scripts/bake_ao.py
t python3 scripts/compose.py
t blender -b -P scripts/export_geom.py
t python3 scripts/swap_lod0.py "$ROOT/assets_source/worlds/mm6/models/mm6_bat.glb" work/geom_export.glb work/stage_lod0.glb Bat
t python3 scripts/apply_textures.py work/stage_lod0.glb export/mm6_bat_lod0.glb
t blender -b -P "$ROOT/tools/build_actor_lods.py" -- export/mm6_bat_lod0.glb export/mm6_bat_lods.glb --mesh-node Bat
t python3 ../mm6_bat_claude/scripts/shrink_shadow_lods.py export/mm6_bat_lods.glb export/mm6_bat.glb
t python3 scripts/carry_variants.py export/mm6_bat.glb
t python3 scripts/viewer_variants.py export/mm6_bat.glb rt
grep -h "LOD triangles" work/log_chain_Bat.txt || true; grep -h "UV_PARITY" work/log_chain_verify_uv.py.txt | cut -c1-200; grep -h COMPOSE work/log_chain_compose.py.txt
