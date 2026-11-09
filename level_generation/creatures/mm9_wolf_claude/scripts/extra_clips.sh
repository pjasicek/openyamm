#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/uv_v3c.blend, the blend build_export.py opens), graft
# them into a copy of the accepted export, floor them as build_runtime.sh floors the accepted clips (tail chain lifted
# first, ground-loop for the idles and the backpedal, raise for the rest, Death2 grounded on a temporary Dead2), then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls (fidget1, wince1, die1) go through the same steps and are compared
# with the installed clips. Usage: TOK=<lease token> scripts/extra_clips.sh (work/pre_clips_export.glb = the export before)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=$(basename "$here" | sed 's/_claude$//')
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
# MM9's RAttack1 carries aware's keys and backpedalrun carries backpedal's (0.13 deg / 0.0000 deg apart, seam closing
# only): bound as attack_ranged2: Aware and backpedal_run: Backpedal, not grafted twice
NEW=(Aware Taunt Fidget2 Hit2 Death2 Backpedal)
ALL=("${NEW[@]}" Dead2 Ctl_Fidget Ctl_Hit Ctl_Death Ctl_Dead)
CTL=(Ctl_Fidget:Fidget Ctl_Hit:Hit Ctl_Death:Death Ctl_Dead:Dead)
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/uv_v3c.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb $(for c in "${ALL[@]}"; do echo --clip $c; done) | tail -1
# Death2/Dead2 are not tail-lifted: the per-key lift spun the tail 125-147 deg in a frame while the wolf lies on its back
# (die2 0.9 s); --ground-death keeps the tail on the floor instead.
Q $G $F work/g0.glb work/g0t.glb --lift-joints $(for c in "${ALL[@]}"; do [[ $c == Death2 || $c == Dead2 ]] || echo $c; done) --lift-only 'Bone34,Bone21,Bone22,Bone23,Bone24' | tail -1
Q $G $F work/g0t.glb work/gc.glb --ground-loop Ctl_Fidget --raise Ctl_Hit --ground-death Ctl_Death Ctl_Dead | tail -1
Q $G $F work/g0t.glb work/g1.glb --ground-loop Aware --ground-loop Fidget2 --ground-loop Backpedal --raise Taunt \
  --raise Hit2 --ground-death Death2 Dead2 | tail -1
for p in "${CTL[@]}"; do echo "control ${p%%:*} vs ${p##*:}"; Q $G ../claude_shared/compare_clips.py work/gc.glb ${p%%:*} $E ${p##*:} | tail -3; done
Q $G $GR $E work/g1.glb export/$name.glb $(for c in "${NEW[@]}"; do echo --clip $c; done) | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
