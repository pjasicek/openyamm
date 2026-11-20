#!/usr/bin/env bash
set -euo pipefail
: "${CREATURE_3D_TOKEN:?claim this creature project first}"
: "${LOD_REPAIR_PYTHON:?Python with pymeshlab and xatlas}"
p=level_generation/creatures/hes_kept_codex
G() { python3 tools/creature_workspace.py run --project "$p" --token "$CREATURE_3D_TOKEN" -- "$@"; }
B() { "$p/scripts/step.sh" "$@"; }
B addons_export
B addons_export_props
for stem in hes_kept_m_ragged hes_kept_m_enforcer; do
 G python3 tools/prepare_actor_glb.py "$p/export/${stem}_lod0.glb" "$p/export/${stem}_runtime_lod0.glb"
 B build_lods "$stem"
 if [[ "$stem" == hes_kept_m_enforcer ]]; then
  B addons_lods
  G cp "$p/export/${stem}_lods_plate.glb" "$p/export/${stem}_lods.glb"
 fi
 G python3 "$p/scripts/shrink_shadow_lods.py" "$p/export/${stem}_lods.glb" "$p/export/${stem}_shadowfix.glb"
 G python3 level_generation/creatures/claude_shared/region_variants.py "$p/export/${stem}_shadowfix.glb" "$p/export/${stem}_variants.glb" "$p/textures/kept_ramps.json" --extra Kept openyamm_specular=1 --extra Kept openyamm_specular_mask=true --extra Kept pbr.metallicFactor=0
 G python3 tools/merge_head_material.py "$p/export/${stem}_variants.glb" "$p/export/${stem}_near.glb"
 G timeout -k 5 1200 python3 "$p/lodrep/repair_glb.py" "$p/export/${stem}_near.glb" "$p/work/lodrep/${stem}_addons_v2" "$p/export/${stem}.glb"
done
G python3 "$p/scripts/addons_material_contract.py"
G python3 "$p/scripts/addons_bind_props.py"
G python3 "$p/scripts/write_bindings.py"
G python3 "$p/scripts/prepare_viewer.py"
G python3 "$p/scripts/check_runtime_floor.py"
G python3 "$p/scripts/validate_runtime.py"
