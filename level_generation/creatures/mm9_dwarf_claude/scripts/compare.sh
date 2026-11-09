#!/bin/bash
# MM9 (Blender, its own skin) above ours (viewer shots). Project folder.
mkdir -p review/cmp
/snap/bin/blender --background --factory-startup --python-exit-code 1 --python scripts/mm9_compare.py -- $PWD/source/true/dwarf_true.glb $PWD/review/cmp/m Stand:0.5 Walk:0.3 Run:0.2 WAttack1:0.33 WAttack1:0.66 Wince1:0.3 Die1:0.9 Die1:1.75 2>&1 | grep -E 'Error|Traceback'
scripts/vs.sh ${1:-dwarf_a} review/cmp o0:Standing:0.5:quarter:body o1:Walking:0.3:quarter:body o2:Running:0.2:quarter:body o3:AttackMelee:0.33:quarter:body o4:AttackMelee:0.66:quarter:body o5:Hit:0.3:quarter:body o6:Death:0.9:quarter:body o7:Dead:0.5:quarter:body
python3 scripts/sheet.py review/sheet_mm9_vs_ours.png 8 300 review/cmp/m_[0-7].png review/cmp/o[0-7].png
