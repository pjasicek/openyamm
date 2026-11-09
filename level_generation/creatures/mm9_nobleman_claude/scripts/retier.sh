#!/bin/bash
# tier materials -> floor -> winding -> install -> viewer, on the existing LODs. Project folder.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; n=mm9_highwayman
$G scripts/tier_materials.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb 2>&1 | tail -1 | cut -c1-120
$G ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -1 | cut -c1-120
$G scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py export/${n}.glb 2>&1 | tail -1
python3 ../../../tools/install_model.py export/${n}.glb --world mm9 2>&1 | tail -1 | cut -c1-100
$G scripts/viewer_tiers.py 2>&1 | tail -1
python3 scripts/make_viewer_manifest.py ${REV:-r8} "hw_a=Cutpurse=review/viewer/hw_a.glb" "hw_b=Burglar=review/viewer/hw_b.glb" "hw_c=Bandit=review/viewer/hw_c.glb" | cut -c1-60
python3 ../../../level_generation/projects/mm9r_common/review_root.py 2>&1 | tail -1 | cut -c1-80
