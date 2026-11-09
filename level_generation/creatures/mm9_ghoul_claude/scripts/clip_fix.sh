"$G" scripts/lower_clip.py work/ghoul_clips1.glb work/ghoul_clips2.glb Running:-0.11 2>&1 | tail -1
"$G" scripts/arm_bump.py work/ghoul_clips2.glb work/ghoul_clips3.glb Hit2:R Hit2:L Hit:L Death:L:0.25 Death2:L:0.2 Death2:R:0.2 2>&1 | grep -E "BUMP|DEPTH|SIGNS|Traceback|Error" | cut -c1-170
cp work/ghoul_clips3.glb work/ghoul_final_clips.glb
