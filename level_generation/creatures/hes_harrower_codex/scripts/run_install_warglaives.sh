#!/usr/bin/env bash
# The warglaives replace the crescents (2026-10-24), up to the refitted attacks and their gates:
# 1. the master, cand_raw.blend, exports, binding, grip JSONs, audits and atlas go to work/before_warglaives_20261024/
#    (first run only);
# 2. warglaive_atlas.py pastes the baked glaive textures into the atlas;
# 3. install_warglaives.py puts the glaives into the master (work/glaive_base.blend, writing the grip JSONs' glaive
#    frame) and into the chain's sources (work/cand_raw.blend);
# 4. run_cands.sh refits A1, B1 and C to the new blades and runs every gate.
# Then, after review: BASE=work/glaive_base.blend run_install_attacks.sh. Env as run_lib.sh.
set -euo pipefail
source "$(dirname "$0")/run_lib.sh"
B=work/before_warglaives_20261024
if [[ ! -e $B/final.blend ]]; then
    mkdir -p "$B/export" "$B/integration" "$B/review" "$B/textures"
    cp work/final.blend work/cand_raw.blend work/grip_pose_L.json work/grip_pose_R.json "$B/"
    cp export/*.glb export/attachments.json "$B/export/"; cp integration/actors.yml "$B/integration/"
    cp review/validation.json review/lod_audit.json review/binding_metrics.json "$B/review/"
    cp textures/hkr_armour_*.png "$B/textures/"
fi
cp "$B"/textures/hkr_armour_*.png textures/          # paste onto the untouched atlas, so reruns are identical
py warglaive_atlas "$W"/scripts/warglaive_atlas.py
grep GLAIVE_ATLAS "$LOG/warglaive_atlas.log"
cp "$B/grip_pose_L.json" "$B/grip_pose_R.json" work/
blend install_glaives install_warglaives.py "$W/$B/final.blend" "$W/work/glaive_base.blend" --write-grip
grep WARGLAIVES "$LOG/install_glaives.log" | cut -c1-600
blend install_glaives_cand install_warglaives.py "$W/$B/cand_raw.blend" "$W/work/cand_raw.blend"
"$W/scripts/run_cands.sh"
