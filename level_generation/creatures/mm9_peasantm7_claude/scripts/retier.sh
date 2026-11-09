#!/bin/bash
# Tiers only (after scripts/tier_pm7.py): region variants -> floor -> mirror -> winding, from export/mm9_pm7_extras.glb of the
# last build_runtime_v2.sh run (the same steps as its tail). Project folder.
set -e
python3 ../claude_shared/region_variants.py export/mm9_pm7_extras.glb export/mm9_pm7_variants.glb textures/pm7_ramps.json \
  --extra PeasantM7 openyamm_specular=0 --extra PeasantM7 pbr.metallicFactor=0
python3 ../claude_shared/floor/floor_fix.py export/mm9_pm7_variants.glb work/mm9_pm7_unmirrored.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -1
python3 scripts/mirror_glb.py work/mm9_pm7_unmirrored.glb export/mm9_pm7.glb
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm9_pm7.glb | tail -1
