#!/usr/bin/env bash
# Rebuild the picked candidate (fix pass: set m = h + the gold goose piece, ladder step r70, chart guard) from the installed GLB
# in before/. Run from anywhere.
# The keep files lock_death / lock_f65 came from the gates of the earlier builds a60 and f65 (contact_lock.py reads
# review/gates_<build>/arm_hand.json); they are kept in work/ and reused here as they are.
set -euo pipefail
cd "$(dirname "$0")/.."
G="../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_GLB=level_generation/creatures/mm9_honkf_reduce_claude/before/mm9_honkf.glb REA_NODE=HonkF $BL -P scripts/import_source.py
REA_PROTECT=Head $BL -P scripts/dump_mesh.py
$G scripts/tex_extract.py
$G scripts/make_sets.py a                                                  # classes + base keep set
scripts/cap.sh $G scripts/honk_contact.py a contact                        # faces under the hands (every clip, 15 Hz)
DRGB=70 DMASK=90 RING=0 $G scripts/paint_edges.py a paint                  # robe faces across a paint boundary
$G scripts/neck_zone.py a neck                                             # robe faces round the neckline
LINED_KEEP=1 KEEP_EXTRA=contact,paint,lock_death,neck,lock_f65 $G scripts/make_sets.py h
$G scripts/goose_keep.py h goose                                          # the gold goose piece (beak, eye)
LINED_KEEP=1 KEEP_EXTRA=contact,paint,lock_death,neck,lock_f65,goose $G scripts/make_sets.py m
MP_CHART=1 SETS=m MP_SEAM_GROUPS=1,2,4,9 MP_GROUPS=1:0.75,2:0.7,3:0.7,4:0.5,5:0.6,6:0.5,7:0.6,9:0.85 MP_TEX_MAX=70 MP_TEX_MEAN=30 \
  scripts/cap.sh $G scripts/mpqem.py before/mm9_honkf.glb 0.7
cp work/mp_r70.npz work/mp_n_r70.npz
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=0.7 $BL -P scripts/reduce_ladder.py > work/ladder_n.log 2>&1
REA_HEIGHT_M=1.909 scripts/cap.sh python3 scripts/compare_ladder.py
scripts/build_mp.sh mp_n_r70 export/mm9_honkf.glb
$G ../claude_shared/reduction_uv_audit.py export/mm9_honkf.glb before/mm9_honkf.glb --json review/uv_audit_n70/audit.json
