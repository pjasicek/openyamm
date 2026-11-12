#!/usr/bin/env bash
# Final gates on export/mm6_thf.glb (project folder): arm and hand, jitter against the raw MM9 clips, grip, motion audit and the audit's
# rebuild numbers, texture quality, winding. Writes review/gates/*.txt and audit_after/*.
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; G=$here/../claude_shared/gltf_venv/bin/python
mkdir -p review/gates audit_after
$G -W ignore scripts/arm_hand_gate.py export/mm6_thf.glb review/gates/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact 2>&1 | grep -v Warning > review/gates/arm_hand.txt
$G -W ignore scripts/jitter_gate.py work/thf_final_clips.glb work/c1.glb review/gates/jitter.json --side "L= L " --side "R= R " 2>&1 | grep -v Warning > review/gates/jitter.txt
$G -W ignore scripts/grip_gate.py export/mm6_thf.glb review/gates/grip.txt > /dev/null 2>&1
python3 ../claude_shared/motion_audit.py export/mm6_thf.glb --out audit_after > /dev/null 2>&1
python3 ../audit_mm678_20261111/fixes/rebuild_measure.py audit_after/mm6_thf.json biped standing=Standing walking=Walk2 run=Jog attack_melee=Attack attack_ranged=AttackRanged cast=Attack hit=Hit fidget=Fidget dying=Death > audit_after/measure.json
$G -W ignore ../claude_shared/texture_quality.py export/mm6_thf.glb --by-bone --json audit_after/texq.json > audit_after/texq.txt 2>&1
$G -W ignore ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm6_thf.glb > review/gates/winding.txt 2>&1
echo GATES DONE
