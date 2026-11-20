from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for view in ['front','left','three_quarter']:
 sys.argv=['rpg_preview.py','--',str(p.parents[2]/'anim_library/humanoid_set/Unarmed.glb'),str(p/'review/source_motion/Unarmed'/view),view,'7','UnarmedDeath1','UnarmedGetHitF1','UnarmedCastDualAttack2','UnarmedIdleAlert1']
 runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
