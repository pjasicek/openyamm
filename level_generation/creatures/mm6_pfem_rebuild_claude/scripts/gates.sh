#!/usr/bin/env bash
# Final gates on export/mm6_pfem.glb (project folder): arm/hand, jitter vs the raw MM9 clips, robe (legs through the skirt), motion audit and
# the audit's rebuild numbers, texture quality, winding. Writes review/gates/*.txt, audit_after/*.
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; G=$here/../claude_shared/gltf_venv/bin/python
$G -W ignore scripts/arm_hand_gate.py export/mm6_pfem.glb review/gates/arm_hand_final.json --side "L= L " --side "R= R " --outer-only --exact 2>&1 | grep -v Warning > review/gates/arm_hand_final.txt
$G -W ignore scripts/jitter_gate.py work/half.glb work/clips.glb review/gates/jitter.json --side "L= L " --side "R= R " 2>&1 | grep -v Warning > review/gates/jitter.txt
$G -W ignore scripts/robe_gate.py export/mm6_pfem.glb review/gates/robe_final.json 2>&1 | grep -v Warning > review/gates/robe_final.txt
python3 ../claude_shared/motion_audit.py export/mm6_pfem.glb --out audit_after > /dev/null 2>&1
python3 ../audit_mm678_20261111/fixes/rebuild_measure.py audit_after/mm6_pfem.json biped standing=Standing walking=Walk2 run=Running attack_melee=Attack attack_ranged=Attack cast=Attack hit=Hit fidget=Fidget dying=Death > audit_after/measure.json
$G -W ignore ../claude_shared/texture_quality.py export/mm6_pfem.glb --by-bone --json audit_after/texq.json > /dev/null 2>&1
$G -W ignore ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm6_pfem.glb > review/gates/winding.txt 2>&1
echo GATES DONE
