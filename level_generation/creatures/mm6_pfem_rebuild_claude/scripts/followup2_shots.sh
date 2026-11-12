#!/usr/bin/env bash
# Follow-up 2 (torso): installed (work/before_followup2) vs fixed viewer shots at identical cameras, tier A; every clip front and right side
# plus waist close-ups -> review/followup2/{installed,fixed}/ and review/followup2/sheet_*.png. Usage: scripts/followup2_shots.sh [tiers]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; repo="$(cd -- "$here/../../.." && pwd)"
G=$here/../claude_shared/gltf_venv/bin/python; S=$repo/level_generation/creatures/claude_shared/texpass_viewer_shots.py
T=${1:-pfem_a}
SPECS=("standF:Standing:0:front:body" "standR:Standing:0:right:body" "standQ:Standing:1.2:quarter:body"
       "waistF:Standing:0:front:body:0,1.05,0.95:0,1.0,0" "waistR:Standing:0:right:body:0.95,1.05,0:0,1.0,0"
       "waistB:Standing:0:back:body:0,1.05,-0.95:0,1.0,0"
       "walkF:Walk2:0.3:front:body" "walkR:Walk2:0.3:right:body" "runF:Running:0.3:front:body" "runR:Running:0.3:right:body"
       "attackF:Attack:0.48:front:body" "attackR:Attack:0.48:right:body" "hitF:Hit:0.3:front:body" "hitR:Hit:0.3:right:body"
       "deathF:Death:1.0:front:body" "deathR:Death:1.0:right:body" "fidgetF:Fidget:1.5:front:body" "fidgetR:Fidget:1.5:right:body")
mkdir -p review/followup2/installed review/followup2/fixed
ti=$(echo $T | sed 's/\([^,]*\)/\1_installed/g'); tf=$(echo $T | sed 's/\([^,]*\)/\1_rebuild/g')
$G -W ignore scripts/viewer_manifest.py installed followup2 > /dev/null
(cd "$repo" && python3 $S shots $here $here/review/followup2/installed $ti "${SPECS[@]}" | tail -1)
$G -W ignore scripts/viewer_manifest.py rebuild ${REV:-followup2} > /dev/null
(cd "$repo" && python3 $S shots $here $here/review/followup2/fixed $tf "${SPECS[@]}" | tail -1)
for t in ${T//,/ }; do
  for f in review/followup2/installed/${t}_installed_*.png; do mv "$f" review/followup2/installed/${t}_${f##*_installed_}; done
  for f in review/followup2/fixed/${t}_rebuild_*.png; do mv "$f" review/followup2/fixed/${t}_${f##*_rebuild_}; done
done
python3 $S sheet review/followup2/sheet_waist.png review/followup2/installed review/followup2/fixed $T standF,standR,waistF,waistR,waistB
python3 $S sheet review/followup2/sheet_clips_front.png review/followup2/installed review/followup2/fixed $T walkF,runF,attackF,hitF,deathF,fidgetF
python3 $S sheet review/followup2/sheet_clips_side.png review/followup2/installed review/followup2/fixed $T walkR,runR,attackR,hitR,deathR,fidgetR
