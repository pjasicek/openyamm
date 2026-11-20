import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/patch_string_export.py'),run_name='__main__')
bow=R/'anim_library/humanoid_set/2Hand Bow.glb';relax=R/'anim_library/humanoid_set/Relax.glb'
refs={'Standing':(bow,'2HandBowIdle'),'Walking':(bow,'2HandBowWalk'),'Running':(relax,'RelaxRunForward'),'Attack':(bow,'2HandBowAttack1'),'Cast':(bow,'2HandBowAttack1'),'Hit':(bow,'2HandBowGetHitF1'),'Death':(bow,'2HandBowDeath1'),'Dead':(bow,'2HandBowDeath1'),'Fidget':(bow,'2HandBowIdle')}
sys.argv=['trace','--',str(P/'export/mm6_lzd_raw.glb')]+[f'{r}={f}:{c}'for r,(f,c)in refs.items()]
runpy.run_path(str(P/'scripts/trace_export.py'),run_name='__main__')
