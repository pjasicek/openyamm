#!/usr/bin/env bash
# Clips MM9's scripts play on Forad Darre (run2-clips-groupD, 2026-10-31; user: only the PeasantMale clips his scripts and
# dialogue play): forad.scr / basemelee.scr (BaseRun.inc: LoopAnim Cower) and ARG_Forad.scr in Thronheim's Argument scene
# (loopanim Sit; Agree, Applause, Sc2_Forad6, Sc2_forad26, each back to Sit; his own FORADDARRE.abc clips). Bow is installed.
# Steps as build_runtime_v2.sh: clips_mm9.py (roles_forad_extra.json, soft joint-offset line) -> hand_rest.py
# (hand_rest_forad_extra.txt) -> graft into the accepted pre-floor export -> floor_fix.py (floor_ops_extra.txt: the seated clips
# stand on their feet, so the seat MM9 sits him on is the map's) -> graft the new clips onto v2/work/pre_clips_export.glb.
set -euo pipefail
cd "$(dirname "$0")/../.."
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
NEW="--clip Cower --clip Sit --clip Agree --clip Applause --clip ArgumentSpeak6 --clip ArgumentSpeak20"
Q $G v2/scripts/clips_mm9.py v2/work/forad_body_tex.glb v2/work/extra_raw.glb v2/scripts/roles_forad_extra.json v2/work/clips_extra.json | tail -1
cur=v2/work/extra_raw.glb; k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); eval "Q $G v2/scripts/hand_rest.py $cur v2/work/extra_rest$k.glb $line" | cut -c1-200; cur=v2/work/extra_rest$k.glb
done < v2/scripts/hand_rest_forad_extra.txt
Q $G $GR v2/export/mm9_forad_extras.glb $cur v2/work/extra_g0.glb $NEW | tail -1
Q $G $F v2/work/extra_g0.glb v2/work/extra_floor.glb $(cat scripts/floor_ops_extra.txt)
Q $G $GR ${EXPORT:-v2/work/pre_clips_export.glb} v2/work/extra_floor.glb v2/work/mm9_forad_grafted.glb $NEW | tail -1
Q $G ../claude_shared/graft_byte_check.py ${EXPORT:-v2/work/pre_clips_export.glb} v2/work/mm9_forad_grafted.glb
