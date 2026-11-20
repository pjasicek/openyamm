#!/bin/bash
# Close-ups framed on the joint, viewer shots: knees, groin, armpits, elbow, neck, head in Cower (crouch), Death end, Dead, Running. Usage: scripts/close.sh <tier>. Project folder.
G=$PWD/../claude_shared/gltf_venv/bin/python; t=$1
SP() { $G -W ignore scripts/close_specs.py export/mm9_nobleman.glb "$@" 2>/dev/null | tr '\n' ' '; }
S=""
for cs in Cower:1.2 Death:1.0 Dead:0.5 Running:0.17; do
  c=${cs%%:*}
  S+=" $(SP ${t}${c}_ $cs "Bip01 L Calf:0.7,-0.1,0.7:0.6" "Bip01 R Calf:-0.7,-0.1,-0.7:0.6" "Bip01 Pelvis:0.1,-0.5,1:0.75" "Bip01 R UpperArm:-1,-0.3,0.5:0.6" "Bip01 L UpperArm:1,-0.3,0.5:0.6" "Bip01 R Forearm:-1,0.2,-0.6:0.55" "Bip01 Neck:0.8,0.2,0.7:0.42" "Bip01 Head:0,-0.25,1:0.42")"
done
echo $S | tr ' ' '\n' > work/spc.txt; split -l 16 -d work/spc.txt work/spc_
for f in work/spc_0?; do scripts/shots.sh $t review/close $(cat $f) | tail -1; done
rm -f work/spc_00 work/spc_01 work/spc_02
python3 scripts/sheet.py review/sheet_closeups_$t.png 8 300 $(for c in Cower Death Dead Running; do for k in 0 1 2 3 4 5 6 7; do echo review/close/${t}${c}_$k.png; done; done)
