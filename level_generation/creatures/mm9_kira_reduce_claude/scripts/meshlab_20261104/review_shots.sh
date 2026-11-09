#!/usr/bin/env bash
# Side-by-side viewer shots, installed vs reduced (project folder): body views in Standing and two motion clips, the face sheet (front
# close-up, three-quarter, true profile, low three-quarter, party distance) in Standing and Fidget, and close-ups of the reduced parts
# (pauldron lames, medallion, belt, knee cops, skirt, hair back, vambraces). -> review/shots/<model>/*.png, review/pair_*.png
# (top row installed, bottom row reduced).
set -uo pipefail
cd "$(dirname "$0")/.."
G="../claude_shared/gltf_venv/bin/python -W ignore"; E=before/mm9_kira.glb
SP() { $G scripts/close_specs.py $E "$@" 2>/dev/null | tr '\n' ' '; }
BODY="bq:Standing:0.5:quarter:body bf:Standing:0.5:front:body bb:Standing:0.5:back:body bs:Standing:0.5:right:body wq:Walking:0.3:quarter:body wf:Walking:0.8:front:body aq:AttackMelee:0.35:quarter:body fq:Fidget:1.5:quarter:body"
FACE="$(TOFF=0,0.075,0.02 SP hs_ Standing:0.5 'Bip01 Head:0,0.05,1:0.42' 'Bip01 Head:-0.7,0.05,0.7:0.42' 'Bip01 Head:-1,0.05,0:0.42' 'Bip01 Head:-0.6,-0.55,0.6:0.42' 'Bip01 Head:0.25,0.35,1:1.6' 'Bip01 Head:0.7,0.05,0.7:0.42' 'Bip01 Head:0,0.1,-1:0.5')"
FACE+=" $(TOFF=0,0.075,0.02 SP hf_ Fidget:1.83 'Bip01 Head:0,0.05,1:0.42' 'Bip01 Head:-0.7,0.05,0.7:0.42' 'Bip01 Head:-1,0.05,0:0.42' 'Bip01 Head:-0.6,-0.55,0.6:0.42' 'Bip01 Head:0.25,0.35,1:1.6')"
DET="$(SP ds_ Standing:0.5 'Bip01 Spine2:0,0.1,1:0.55' 'Bip01 R UpperArm:-1,0.3,0.4:0.45' 'Bip01 L UpperArm:1,0.3,0.4:0.45' 'Bip01 Pelvis:0,0,1:0.6' 'Bip01 Pelvis:0,0,-1:0.6' 'Bip01 R Calf:-0.3,0.1,1:0.45' 'Bip01 L Calf:0.6,0.2,1:0.5' 'Bip01 Spine2:0,0.2,-1:0.6' 'Bip01 R Forearm:-0.7,0.2,0.7:0.4' 'Bip01 L Forearm:0.7,0.2,0.7:0.4')"
DET+=" $(SP dw_ Walking:0.3 'Bip01 Pelvis:-0.6,0,0.8:0.75' 'Bip01 Pelvis:0.6,0,-0.8:0.75') $(SP dd_ Dead:0.5 'Bip01 Spine2:0,1,0.3:1.1')"
for M in kira_installed kira_reduced; do
  for S in "$BODY" "$FACE" "$DET"; do M=$M scripts/shots.sh review/shots/$M $S | tail -1; done
done
pair() { out=$1; shift; COLS=$# python3 scripts/sheet.py review/pair_$out.png $(for n in "$@"; do echo review/shots/kira_installed/$n.png; done) $(for n in "$@"; do echo review/shots/kira_reduced/$n.png; done); }
pair body bq bf bb bs; pair motion wq wf aq fq
pair face_stand hs_0 hs_1 hs_2 hs_3 hs_4; pair face_fidget hf_0 hf_1 hf_2 hf_3 hf_4; pair head_back hs_5 hs_6
pair detail_a ds_0 ds_1 ds_2 ds_3 ds_4; pair detail_b ds_5 ds_6 ds_7 ds_8 ds_9; pair detail_c dw_0 dw_1 dd_0
echo SHOTS_DONE
