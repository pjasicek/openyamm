#!/usr/bin/env bash
# After the Meshy body return: UV parity, body raster, compose (atlas body half), geometry export, swap into the
# installed GLB (clips, variants, head set kept), atlases swapped in, LODs, shadow LODs, variant mappings, viewer (rt).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
t(){ local s=$(date +%s); "$@" > "$P/work/log_chain_$(basename "${@: -1}").txt" 2>&1 || { echo "FAILED $*"; tail -20 "$P/work/log_chain_$(basename "${@: -1}").txt"; exit 1; }; echo "$* $(( $(date +%s) - s ))s" | cut -c1-120; }
t python3 scripts/verify_uv.py
t blender -b -P scripts/body_raster.py
t python3 scripts/compose.py
t blender -b -P scripts/export_geom.py
t python3 scripts/swap_lod0.py "$ROOT/assets_source/worlds/mm6/models/mm6_djn.glb" work/geom_export.glb work/stage_lod0.glb Body
t python3 scripts/apply_textures.py work/stage_lod0.glb export/mm6_djn_lod0.glb
t blender -b -P "$ROOT/tools/build_actor_lods.py" -- export/mm6_djn_lod0.glb export/mm6_djn_lods.glb --mesh-node Body
t python3 ../mm6_djn_claude/scripts/shrink_shadow_lods.py export/mm6_djn_lods.glb export/mm6_djn.glb
t python3 scripts/carry_variants.py export/mm6_djn.glb
t python3 scripts/viewer_variants.py export/mm6_djn.glb rt
grep -h "LOD triangles" work/log_chain_Body.txt || true; cat work/log_chain_verify_uv.py.txt; grep -h COMPOSE work/log_chain_compose.py.txt
