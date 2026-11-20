#!/usr/bin/env bash
# Resume from the retained returned-UV masters. No Meshy calls or installation.
set -euo pipefail
p=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
repo=$(cd -- "$p/../../.." && pwd)
cd "$repo"
: "${CREATURE_3D_TOKEN:?claim this creature workspace first}"
: "${LOD_REPAIR_PYTHON:?Python with pymeshlab and xatlas}"
G() { python3 tools/creature_workspace.py run --project "$p" --token "$CREATURE_3D_TOKEN" -- "$@"; }
B() { "$p/scripts/step.sh" "$@"; }
G python3 "$p/scripts/compose_textures.py"
KEPT_BODY=male KEPT_STYLE=ragged B export_runtime
B fit_collar_motion
B lower_collar 0 0.5
B fit_collar_shape
B correct_collar_keys
B floor_equipment
KEPT_BODY=male KEPT_STYLE=freed B export_runtime
KEPT_BODY=female KEPT_STYLE=freed B export_runtime
for stem in hes_kept_m_ragged hes_kept_m_freed hes_kept_f_freed; do
 G python3 tools/prepare_actor_glb.py "$p/export/${stem}_lod0.glb" "$p/export/${stem}_runtime_lod0.glb"
 B build_lods "$stem"
 G python3 "$p/scripts/shrink_shadow_lods.py" "$p/export/${stem}_lods.glb" "$p/export/${stem}_shadowfix.glb"
 if [[ "$stem" == hes_kept_m_ragged ]]; then
  G python3 level_generation/creatures/claude_shared/region_variants.py "$p/export/${stem}_shadowfix.glb" "$p/export/${stem}_variants.glb" "$p/textures/kept_ramps.json" --extra Kept openyamm_specular=1 --extra Kept openyamm_specular_mask=true --extra Kept pbr.metallicFactor=0
 else
  G cp "$p/export/${stem}_shadowfix.glb" "$p/export/${stem}_variants.glb"
 fi
 G python3 tools/merge_head_material.py "$p/export/${stem}_variants.glb" "$p/export/${stem}_near.glb"
 G timeout -k 5 1200 python3 "$p/lodrep/repair_glb.py" "$p/export/${stem}_near.glb" "$p/work/lodrep/$stem" "$p/export/${stem}.glb"
done
B export_attachments
G python3 "$p/scripts/bind_attachments.py"
B check_attachments
B check_prop_floor
B verify_final_master
G python3 "$p/scripts/write_bindings.py"
G python3 "$p/scripts/prepare_viewer.py"
G python3 "$p/scripts/check_runtime_floor.py"
G python3 "$p/scripts/validate_runtime.py"
