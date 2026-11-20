#!/usr/bin/env bash
# Floor the Trot as the wolf's build_runtime.sh / extra_clips.sh floor their clips (the tail chain lifted first, then
# --raise: a run never below the floor, its flights kept), then graft only Trot onto the installed source so meshes,
# LODs, variants and the accepted clips stay byte for byte. Usage: scripts/finish.sh (after wolf_trot.py)
set -euo pipefail
cd "$(dirname "$0")/.."
G=../../claude_shared/gltf_venv/bin/python; F=../../claude_shared/floor/floor_fix.py; GR=../../claude_shared/graft_clips.py
SRC=${SRC:-work/rollback/mm9_wolf.glb}
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q $G $GR $SRC work/wolf_clips.glb work/g0.glb --clip Trot | tail -1
Q $G $F work/g0.glb work/g0t.glb --lift-joints Trot --lift-only 'Bone34,Bone21,Bone22,Bone23,Bone24' | tail -1
Q $G $F work/g0t.glb work/g1.glb --raise Trot | tail -1
Q $G $GR $SRC work/g1.glb export/mm9_wolf.glb --clip Trot | tail -1
Q $G ../../claude_shared/graft_byte_check.py $SRC export/mm9_wolf.glb
