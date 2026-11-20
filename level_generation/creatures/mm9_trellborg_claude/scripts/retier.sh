#!/usr/bin/env bash
# From the tier step: images changed only. Project folder: REV=rN scripts/retier.sh
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_trellborg
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q "$G" scripts/tier_materials.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb | tail -1 | cut -c1-120
Q "$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -1 | cut -c1-120
Q "$G" scripts/fix_winding.py export/${n}.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -1 | cut -c1-100
Q "$G" scripts/viewer_tiers.py | tail -1
python3 scripts/make_viewer_manifest.py ${REV:-r2} "trell_a=Trellborg=review/viewer/trell_a.glb" "trell_b=Kin Trellborg=review/viewer/trell_b.glb" "trell_c=Ancient Trellborg=review/viewer/trell_c.glb" | cut -c1-50
