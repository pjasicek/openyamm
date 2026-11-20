#!/usr/bin/env bash
# Rebuild the picked candidate (set i, ladder step r55) from the installed GLB in before/. Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."
G="../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_GLB=level_generation/creatures/mm9_zombie_reduce_claude/before/mm9_zombie.glb REA_NODE=Zombie $BL -P scripts/import_source.py
REA_PROTECT=Head $BL -P scripts/dump_mesh.py
$G scripts/glb_parts.py; $G scripts/tex_extract.py
$G scripts/make_sets.py a                                            # classes + base keep set
R=0.035 scripts/cap.sh $G scripts/hand_hand.py a hand_hand           # hand faces touching the other hand
R=0.03 scripts/cap.sh $G scripts/hand_contact.py a hand_contact3     # body faces under the hands (all clips)
R=0.06 HZ=48 CLIPS=Death2 scripts/cap.sh $G scripts/hand_contact.py a hand_death2
python3 - <<'PY'
import json, numpy as np
s = np.load('work/glb_sets_a.npz'); C = json.load(open('work/classes.json'))['names']; tr = s['cls'] == C.index('trousers')
np.save('work/hand_legs2.npy', (np.load('work/hand_contact3.npy') | np.load('work/hand_death2.npy')) & tr)
PY
KEEP_EXTRA=hand_hand,hand_legs2 $G scripts/make_sets.py i
SETS=i MP_GROUPS=1:0.65,2:0.65,3:0.8,4:0.7,5:0.75 scripts/run_mp.sh i 0.55
scripts/build_mp.sh mp_i_r55 export/mm9_zombie.glb
