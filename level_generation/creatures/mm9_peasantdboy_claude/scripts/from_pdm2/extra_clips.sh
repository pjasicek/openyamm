#!/usr/bin/env bash
# Clips MM9's scripts play on the ShopkeeperHuman2MaleA body (run2-clips-groupD, 2026-10-31; user: only the PeasantMale
# clips their scripts and dialogue play): NPCbase.scr / retainer.scr (BaseRun.inc: LoopAnim Cower) and Trislan.scr
# (Guberland play: conv1, conv2 = the installed Talk, conv3, Play_Death -> Play_getup, Bow). Steps as build_runtime_v2.sh:
# clips_mm9.py (roles_annud_extra.json, soft joint-offset line) -> arm_clear.py twice (Cower, Conv3, PlayDeath; PlayGetUp is
# left out: its 40 deg turn jittered 7.9 deg/f over MM9 for a hand at the head) -> hand_rest.py (hand_rest_annud_extra.txt)
# -> graft into the accepted pre-floor export -> floor_fix.py (floor_ops_extra.txt; PlayDeath grounds onto PlayDead, its last
# pose, which is not grafted; PlayGetUp and PlayDeath smoothed 0.08 s: per-key grounding shook the shoulders 15 and 12 mm/f2
# over MM9, smoothed 1.4 and 1.1, at a 2.7 cm dip) -> graft the new clips onto v2/work/pre_clips_export.glb (the installed export before this).
set -euo pipefail
cd "$(dirname "$0")/../.."
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
NEW="--clip Cower --clip Conv1 --clip Conv3 --clip Bow --clip PlayDeath --clip PlayGetUp"
C=Cower,Conv3,PlayDeath; L=Standing,Walking,Running,Cower,Conv1,Conv3
Q $G v2/scripts/clips_mm9.py v2/work/annud_body_tex.glb v2/work/extra_raw.glb v2/scripts/roles_annud_extra.json v2/work/clips_extra.json | tail -1
Q $G v2/scripts/arm_clear.py v2/work/extra_raw.glb v2/work/extra_clear1.glb --side "L= L " --side "R= R " --iter 8 --margin 0.012 --max-deg 40 --clips $C --loops $L --skip Dead,PlayDead | cut -c1-120
Q $G v2/scripts/arm_clear.py v2/work/extra_clear1.glb v2/work/extra_clear.glb --side "L= L " --side "R= R " --iter 8 --margin 0.015 --max-deg 40 --clips $C --loops $L --skip Dead,PlayDead | cut -c1-120
cur=v2/work/extra_clear.glb; k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); eval "Q $G v2/scripts/hand_rest.py $cur v2/work/extra_rest$k.glb $line" | cut -c1-200; cur=v2/work/extra_rest$k.glb
done < v2/scripts/hand_rest_annud_extra.txt
Q $G $GR v2/export/mm9_annud_extras.glb $cur v2/work/extra_g0.glb $NEW --clip PlayDead | tail -1
Q $G $F v2/work/extra_g0.glb v2/work/extra_floor.glb $(cat scripts/floor_ops_extra.txt) --ground-death PlayDeath PlayDead
Q $G $GR ${EXPORT:-v2/work/pre_clips_export.glb} v2/work/extra_floor.glb v2/work/mm9_annud_grafted.glb $NEW | tail -1
Q $G ../claude_shared/graft_byte_check.py ${EXPORT:-v2/work/pre_clips_export.glb} v2/work/mm9_annud_grafted.glb
