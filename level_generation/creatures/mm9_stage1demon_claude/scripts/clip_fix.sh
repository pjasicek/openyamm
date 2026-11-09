# sourced by rebuild.sh: hands out of the body by one smooth bump per contact (arm_bump.py, from mm9_ghoul_claude)
"$G" scripts/arm_bump.py work/clips1.glb work/clips2.glb ${BUMPS:-Fidget:L:0.4 AttackMelee2:L:0.35 AttackRanged:R DodgeLeft:L:0.3 DodgeLeft:R DodgeRight:L Hit:R Death:L:0.5 Death:R:0.25} 2>&1 | grep -E "BUMP|DEPTH|Traceback|Error" | cut -c1-170
cp work/clips2.glb work/final_clips.glb
