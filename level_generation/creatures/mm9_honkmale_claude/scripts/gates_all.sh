#!/usr/bin/env bash
cd /home/pjasicek/github/OpenYAMM
C=level_generation/creatures; G=$C/mm9_honkmale_claude/scripts
one() { n=$1; p=$2; ref=$3; tok=$4
 ( cd $C/$p; E=v2/export/mm9_$n.glb
   python3 v2/scripts/jitter_gate.py $E $ref review/gates/jitter.json --side "L= L " --side "R= R " > review/gates/jitter.txt 2>&1 &
   python3 v2/scripts/arm_hand_gate.py $E review/gates/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact > review/gates/arm_hand.txt 2>&1 &
   python3 ../claude_shared/detached_parts_audit.py $E > review/gates/detached.txt 2>&1 &
   python3 ../claude_shared/flat_shading_check.py $E > review/gates/flat.txt 2>&1 &
   wait )
 python3 $G/collapse_gate.py $C/$p/v2/export/mm9_$n.glb $C/$p/review/gates/collapse_gate.json > $C/$p/review/gates/collapse_gate.txt 2>&1 &
 python3 $G/robe_gate.py $C/$p/v2/export/mm9_$n.glb $C/$p/review/gates/robe_gate.json 2>/dev/null > $C/$p/review/gates/robe_gate.txt &
 python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $C/$p/v2/export/mm9_$n.glb > $C/$p/review/gates/winding.txt 2>&1 &
 tools/run_creature_blender.sh --token $tok $C/$p/v2/scripts/sleeve_gate.py $PWD/$C/$p/v2/export/mm9_$n.glb $PWD/$C/$p/review/gates/sleeve_gate.json Bip01 24 front,above34,below,q34 > $C/$p/review/gates/sleeve.txt 2>&1 &
 wait
}
one honkm mm9_honkmale_claude v2/work/mm9_honkm_clips.glb 3ea69b82674b427da896431e536c8794 &
one honkf mm9_honkfemale_claude v2/work/mm9_honkf_armout.glb f2b780ca9f9742ebb7f6c597532e62a2 &
wait; echo GATES DONE
