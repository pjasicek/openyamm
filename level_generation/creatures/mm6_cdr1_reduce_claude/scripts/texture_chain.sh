#!/usr/bin/env bash
# After the Meshy returns (and any geometry-only edit of work/uv_master.blend that keeps the UVs): compose, geometry
# export, swap into the head-unified installed GLB, burn maps, textures + ramps, LODs, intact wings, shadow LODs,
# variant mappings, viewer tiers (tag rt).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
t(){ local s=$(date +%s); "$@" > "$P/work/log_chain_$(basename "$1")_$(basename "${@: -1}").txt" 2>&1 || { echo "FAILED $*"; tail -20 "$P/work/log_chain_$(basename "$1")_$(basename "${@: -1}").txt"; exit 1; }; echo "$* $(( $(date +%s) - s ))s" | cut -c1-140; }
t python3 scripts/compose.py
t blender -b -P scripts/export_geom.py
t python3 scripts/swap_lod0.py export/mm6_cdr1_unified.glb work/geom_export.glb work/stage_lod0.glb Body
(cd ../claude_shared && t python3 bake_burn_maps.py "$P/work/stage_lod0.glb" "$P/textures/cdr1r" --node Body \
  --material DragonBody_A=body --material DragonHead_A=head --material DragonWings_A=wings --open DragonWings_A \
  --fast DragonWings_A=0.5 --ignite Head Tail8 Tail9)
t python3 scripts/apply_textures.py work/stage_lod0.glb export/mm6_cdr1_lod0.glb
t blender -b -P "$ROOT/tools/build_actor_lods.py" -- export/mm6_cdr1_lod0.glb export/mm6_cdr1_lods.glb --mesh-node Body
t python3 scripts/preserve_wing_lods.py export/mm6_cdr1_lods.glb
t python3 ../mm6_cdr1_claude/scripts/shrink_shadow_lods.py export/mm6_cdr1_lods.glb export/mm6_cdr1.glb
t python3 scripts/carry_variants.py export/mm6_cdr1.glb
t python3 scripts/viewer_variants.py export/mm6_cdr1.glb rt
grep -h "LOD triangles" work/log_chain_blender_Body.txt || true
