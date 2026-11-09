#!/usr/bin/env bash
# Review-viewer GLBs after build_runtime_pboy.sh (project folder): tiers a and b from the delivered body; tier e from an
# unsplit copy (elf ears kept in the body, as the game draws body + ear attachment). Usage: scripts/viewer.sh <revision>
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
"$V" scripts/tier_head.py work/mm9_pboy_rv.glb work/mm9_pboy_full_tiers.glb PeasantBoyHead pboy_b=pboyb_tp pboy_e=pboye_tp 2>/dev/null
python3 scripts/set_material_extras.py work/mm9_pboy_full_tiers.glb work/mm9_pboy_full_extras.glb openyamm_specular=0 pbr.metallicFactor=0 >/dev/null
python3 ../claude_shared/floor/floor_fix.py work/mm9_pboy_full_extras.glb work/mm9_pboy_full_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -1
$V scripts/mirror_glb.py work/mm9_pboy_full_floor.glb work/mm9_pboy_full.glb 2>/dev/null | tail -1
"$V" scripts/viewer_tiers.py export/mm9_pboy.glb pboy_a,pboy_b 2>/dev/null
"$V" scripts/viewer_tiers.py work/mm9_pboy_full.glb pboy_e 2>/dev/null
python3 scripts/make_viewer_manifest.py "$1" "pboy_a=Boy a (row 69 Commoner Child; PEASANTBOY1)=review/viewer/pboy_a.glb" \
  "pboy_b=Boy b (row 70 Townsfolk Child; PEASANTBOY3)=review/viewer/pboy_b.glb" \
  "pboy_e=Boy e, elf (row 73 Commoner Child; PEASANTBOY2 + elf ear attachment)=review/viewer/pboy_e.glb" | cut -c1-80
