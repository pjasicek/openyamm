#!/usr/bin/env bash
# Full gate set on export/mm9_peasanthof<k>.glb (finishing round 2026-11-04): gates_phof.sh + sleeve poke + robe + see-through.
# Usage (project dir): scripts/finish_gates.sh <out name> <1|2>
set -u
d=$1; k=$2; G=export/mm9_peasanthof$k.glb; O=review/gates/$d; mkdir -p $O
CAP="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0"
sha256sum $G > $O/glb.sha256
bash scripts/gates_phof.sh $d $k
$CAP python3 scripts/sleeve_poke_gate.py $G $O/sleeve.json > $O/sleeve.txt 2>&1
$CAP python3 scripts/robe_gate.py $G $O/robe.json > $O/robe.txt 2>&1
# HOF2: the double-layer dress makes robe_gate flag legs between the lining and the outer dress; robe_diag counts only
# leg vertices with no dress face further out along a horizontal ray (visible through the dress)
if [[ $k == 2 ]]; then $CAP python3 scripts/robe_diag.py $G all 2>&1 | grep ROBE_DIAG > $O/robe_visible.txt; fi
here=$(pwd); (cd ../../.. && level_generation/creatures/mm9_peasanthof_claude/scripts/bld.sh "SEE_THROUGH" \
  level_generation/creatures/mm9_peasanthof_claude/scripts/see_through_gate.py "$here/$G" "$here/$O/see_through.json" > "$here/$O/see_through.txt" 2>&1)
echo ALL GATES DONE $d
