#!/bin/bash
# after texture edits only: skins -> floor -> tone -> viewer. Project folder. scripts/quick_skins.sh <rev>
. scripts/env.sh; n=mm9_troglodyte; L=../claude_shared
"$G" $L/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins0.glb textures/trog_ramps.json --extra Trog openyamm_specular=0 --extra Trog pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-140
"$G" ../mm9_skeleton_claude/scripts/drop_tier_ramps.py export/${n}_skins0.glb export/${n}_skins1.glb _B 2>&1 | tail -1 | cut -c1-140
"$G" scripts/tier_c.py export/${n}_skins1.glb export/${n}_skins.glb 2>&1 | tail -1 | cut -c1-120
"$G" $L/floor/floor_fix.py export/${n}_skins.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -1 | cut -c1-120
"$G" scripts/fix_winding.py export/${n}_floor.glb export/${n}_w.glb 2>&1 | tail -1 | cut -c1-120
"$G" scripts/tone.py export/${n}_w.glb export/${n}.glb 2>&1 | tail -1 | cut -c1-160
rm -f export/${n}_lods.geometry.glb
scripts/viewer_update.sh $1
