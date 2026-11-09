import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['retarget_mixamo','--',str(P/'work/pilots_v6.blend'),str(P/'work/death_raw.blend'),'anim_library/mixamo/Mutant Dying.fbx:DeathRaw']
runpy.run_path('level_generation/creatures/mm6_bar1_claude/scripts/retarget_mixamo.py',run_name='__main__')
runpy.run_path(str(P/'scripts/finish_motion.py'),run_name='__main__')
