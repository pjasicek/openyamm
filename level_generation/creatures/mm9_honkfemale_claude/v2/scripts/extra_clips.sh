#!/usr/bin/env bash
# Dropped-clip pass (2026-10-31): the MM9 clips the accepted build left out, built through the same clip steps as build_runtime_v2.sh
# (clips_mm9 -> [arm_offset] -> hand_rest -> wrist_fix -> [arm_pulses] -> floor -> clip_relax -> mirror) and grafted onto the installed
# export with graft_clips.py, so its meshes, LODs, variants and accepted clips stay byte for byte. Project folder:
#   [TARGET=<installed glb before the pass>] v2/scripts/extra_clips.sh <prefix: honkm|honkf> <mm9 source glb>  -> v2/work/mm9_<prefix>_grafted.glb
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$here"
n=$1; SRC=$2; G=../claude_shared/gltf_venv/bin/python
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q $G v2/scripts/clips_mm9.py v2/work/${n}_body_tex.glb v2/work/extra_clips.glb v2/scripts/roles_${n}_extra.json v2/work/extra_clips.json | tail -1
cur=v2/work/extra_clips.glb
if [[ -f v2/scripts/arm_offset_${n}.txt ]]; then Q $G v2/scripts/arm_offset.py $cur v2/work/extra_armout.glb $(cat v2/scripts/arm_offset_${n}.txt) | tail -1; cur=v2/work/extra_armout.glb; fi
k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); eval "Q $G v2/scripts/hand_rest.py $cur v2/work/extra_rest${k}.glb $line" | cut -c1-160; cur=v2/work/extra_rest${k}.glb
done < v2/scripts/hand_rest_${n}_extra.txt
Q $G v2/scripts/wrist_fix.py $cur v2/work/extra_wrist.glb $SRC | cut -c1-60
cur=v2/work/extra_wrist.glb
if [[ -f v2/scripts/arm_pulses_${n}_extra.json ]]; then Q $G v2/scripts/arm_pulses.py apply $cur v2/work/extra_pulsed.glb v2/scripts/arm_pulses_${n}_extra.json | tail -1; cur=v2/work/extra_pulsed.glb; fi
Q $G ../claude_shared/floor/floor_fix.py $cur v2/work/extra_floor.glb $(cat scripts/floor_ops_extra.txt) | tail -14
Q $G v2/scripts/clip_relax.py v2/work/extra_floor.glb v2/work/extra_relax.glb $(cat v2/scripts/clip_relax_${n}_extra.txt) | tail -3
Q $G v2/scripts/mirror_glb.py v2/work/extra_relax.glb v2/work/extra_mirrored.glb | tail -1
clips=$($G -c "import json; print(' '.join('--clip ' + r for r in json.load(open('v2/scripts/roles_${n}_extra.json'))['roles'] if r not in ('Standing', 'Death')))")
Q $G ../claude_shared/graft_clips.py ${TARGET:-v2/export/mm9_${n}.glb} v2/work/extra_mirrored.glb v2/work/mm9_${n}_grafted.glb $clips | tail -1
