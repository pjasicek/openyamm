#!/usr/bin/env bash
# Texture/tier-only tail of build_runtime_pm1.sh (mesh, weights and clips unchanged): region variants -> tier head ->
# extras -> floor fix -> winding -> viewer GLBs. Usage (project folder): scripts/retier.sh <revision>
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
"$V" ../claude_shared/region_variants.py export/mm9_pm1_lods_shadowfix.glb work/mm9_pm1_rv.glb textures/pm1_ramps.json 2>/dev/null | tail -1 | cut -c1-200
"$V" scripts/tier_head.py work/mm9_pm1_rv.glb work/mm9_pm1_tiers.glb PeasantM1Head pm1_b=pm1b_tp 2>/dev/null
python3 scripts/set_material_extras.py work/mm9_pm1_tiers.glb export/mm9_pm1_extras.glb openyamm_specular=0 pbr.metallicFactor=0
python3 ../claude_shared/floor/floor_fix.py export/mm9_pm1_extras.glb work/mm9_pm1_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -1
# true handedness (mirror_glb.py, as mm9_peasantm1d_claude on the same skeleton): convert_abc_model.py keeps LithTech's
# left-handed numbers, so the unmirrored build (work/mm9_pm1_floor.glb) is the game's actor in a mirror
$V scripts/mirror_glb.py work/mm9_pm1_floor.glb export/mm9_pm1.glb | tail -1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm9_pm1.glb | tail -1
"$V" scripts/viewer_tiers.py 2>/dev/null
python3 scripts/make_viewer_manifest.py "$1" "pm1_a=Tier A (rows 43, 296; PEASANTM1A)=review/viewer/pm1_a.glb" "pm1_b=Tier B (row 56 Prisoner; PEASANTM1B)=review/viewer/pm1_b.glb" | cut -c1-80
