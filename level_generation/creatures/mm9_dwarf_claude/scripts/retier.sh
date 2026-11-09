#!/bin/bash
# ramps -> floor -> winding -> [install] -> viewer, on the existing LODs. Project folder.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; n=mm9_dwarf
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q $G scripts/tier_dwarf.py | grep -E 'share|RAMPS|Traceback'
Q "$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb textures/dwarf_ramps.json \
  --extra DwarfTorso openyamm_specular=0 --extra DwarfLimbs openyamm_specular=0 --extra DwarfHead openyamm_specular=0 --extra DwarfTorso pbr.metallicFactor=0 --extra DwarfLimbs pbr.metallicFactor=0 --extra DwarfHead pbr.metallicFactor=0 \
  --extra DwarfWeapon openyamm_specular=0.3 --extra DwarfWeapon pbr.metallicFactor=0.35 | tail -1 | cut -c1-160
Q "$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/fix_winding.py export/${n}.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
Q "$G" ../../decorations/mm8_3d/animated/scripts/check_winding.py export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 ../../../tools/install_model.py export/${n}.glb --world mm9 2>&1 | tail -1 | cut -c1-100; fi
Q "$G" scripts/viewer_tiers.py | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r5} "dwarf_a=Dwarven Guard=review/viewer/dwarf_a.glb" "dwarf_b=Dwarven Soldier=review/viewer/dwarf_b.glb" "dwarf_c=Dwarven Commander=review/viewer/dwarf_c.glb" | cut -c1-60
